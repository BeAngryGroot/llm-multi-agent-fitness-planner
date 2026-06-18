import os
import json
import logging
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from pymongo import MongoClient

# LangSmith integration
from langsmith import traceable

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_community.llms import Tongyi

# Import existing agent classes
from .agents import (
    ProfileManagerAgent,
    MealPlannerAgent,
    WorkoutPlannerAgent,
    PlanSummaryAgent,
    UserProfile,
    MealPlanRequest,
    WorkoutPlanRequest,
    get_mongo_client,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("langgraph_fitness_agents")

langgraph_agents = APIRouter()


# LangGraph State Definition
class FitnessState(TypedDict):
    """State for the fitness planning workflow"""

    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    user_profile: Optional[Dict[str, Any]]
    meal_plan: Optional[Dict[str, Any]]
    workout_plan: Optional[Dict[str, Any]]
    summary: Optional[str]
    current_step: str
    errors: List[str]
    preferences: Dict[str, Any]


# Pydantic models for API
class LangGraphFitnessRequest(BaseModel):
    user_id: str
    user_profile: Optional[UserProfile] = None
    meal_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    workout_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    generate_meal_plan: bool = True
    generate_workout_plan: bool = True
    use_o3_mini: bool = True
    use_full_database: bool = False


class LangGraphFitnessResponse(BaseModel):
    user_id: str
    workflow_status: str
    user_profile: Optional[Dict[str, Any]] = None
    meal_plan: Optional[Dict[str, Any]] = None
    workout_plan: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    execution_steps: List[str] = []
    errors: List[str] = []
    generated_at: datetime


class FitnessWorkflow:
    """LangGraph workflow orchestrator for fitness planning"""

    def __init__(self, use_o3_mini: bool = True, use_full_database: bool = False):
        self.profile_agent = ProfileManagerAgent()
        self.meal_agent = MealPlannerAgent(use_o3_mini=use_o3_mini, use_full_database=use_full_database)
        self.workout_agent = WorkoutPlannerAgent()
        self.summary_agent = PlanSummaryAgent()
        self.use_o3_mini = use_o3_mini
        self.use_full_database = use_full_database

        # Initialize LLM for coordination
        self.coordinator_llm = Tongyi(
            model="qwen-turbo", 
            temperature=0.3, 
            api_key=os.getenv("TONGYI_API_KEY")
        )

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        workflow = StateGraph(FitnessState)

        # Add nodes for each step
        workflow.add_node("profile_manager", self._manage_profile)
        workflow.add_node("meal_planner", self._plan_meals)
        workflow.add_node("workout_planner", self._plan_workout)
        workflow.add_node("plan_coordinator", self._coordinate_plans)
        workflow.add_node("summary_generator", self._generate_summary)

        # Define the workflow edges
        workflow.set_entry_point("profile_manager")

        # Conditional routing based on preferences
        workflow.add_conditional_edges(
            "profile_manager",
            self._route_after_profile,
            {
                "meal_and_workout": "meal_planner",
                "meal_only": "meal_planner",
                "workout_only": "workout_planner",
                "error": END,
            },
        )

        # Routing from meal planner
        workflow.add_conditional_edges(
            "meal_planner",
            self._route_after_meal_plan,
            {
                "workout_next": "workout_planner",
                "coordinate_next": "plan_coordinator",
                "error": END,
            },
        )

        # Routing from workout planner
        workflow.add_conditional_edges(
            "workout_planner",
            self._route_after_workout_plan,
            {
                "coordinate_next": "plan_coordinator",
                "error": END,
            },
        )

        # From coordinator to summary
        workflow.add_edge("plan_coordinator", "summary_generator")

        # From summary to end
        workflow.add_edge("summary_generator", END)

        return workflow

    def _route_after_profile(self, state: FitnessState) -> str:
        """Route based on profile processing results"""
        if state.get("errors"):
            return "error"

        generate_meal = state.get("preferences", {}).get("generate_meal_plan", True)
        generate_workout = state.get("preferences", {}).get("generate_workout_plan", True)

        if generate_meal and generate_workout:
            return "meal_and_workout"
        elif generate_meal:
            return "meal_only"
        elif generate_workout:
            return "workout_only"
        else:
            return "error"

    def _route_after_meal_plan(self, state: FitnessState) -> str:
        """Route based on meal plan results"""
        if state.get("errors"):
            return "error"

        generate_workout = state.get("preferences", {}).get("generate_workout_plan", True)
        if generate_workout:
            return "workout_next"
        else:
            return "coordinate_next"

    def _route_after_workout_plan(self, state: FitnessState) -> str:
        """Route based on workout plan results"""
        if state.get("errors"):
            return "error"
        return "coordinate_next"

    async def _manage_profile(self, state: FitnessState) -> Dict[str, Any]:
        """Manage user profile"""
        try:
            user_id = state["user_id"]
            user_profile_data = state.get("user_profile")

            # If profile data is provided, update it
            if user_profile_data:
                profile = UserProfile(**user_profile_data)
                updated_profile = await self.profile_agent.update_profile(profile)
                profile_dict = updated_profile.model_dump()
            else:
                # Try to get existing profile
                client = get_mongo_client()
                db = client[os.getenv("MONGO_DB_NAME", "usda_nutrition")]
                profiles = db["user_profiles"]
                profile_dict = profiles.find_one({"user_id": user_id})
                client.close()

                if not profile_dict:
                    raise ValueError("User profile not found and no profile data provided")

                profile_dict.pop("_id", None)

            return {
                "user_profile": profile_dict,
                "current_step": "profile_managed",
                "errors": [],
            }
        except Exception as e:
            logger.error(f"Error in profile management: {str(e)}")
            return {
                "errors": [f"Profile management failed: {str(e)}"],
                "current_step": "error",
            }

    async def _plan_meals(self, state: FitnessState) -> Dict[str, Any]:
        """Generate meal plan"""
        try:
            user_id = state["user_id"]
            profile_dict = state.get("user_profile")

            if not profile_dict:
                raise ValueError("User profile not available for meal planning")

            profile = UserProfile(**profile_dict)
            meal_preferences = state.get("preferences", {}).get("meal_preferences", {})

            meal_request = MealPlanRequest(
                user_id=user_id,
                meal_count=meal_preferences.get("meal_count", 5),
                days=meal_preferences.get("days", 7),
                preferences=meal_preferences,
            )

            meal_plan = await self.meal_agent.generate_meal_plan(profile, meal_request)

            return {
                "meal_plan": meal_plan,
                "current_step": "meals_planned",
                "errors": [],
            }
        except Exception as e:
            logger.error(f"Error in meal planning: {str(e)}")
            return {
                "errors": [f"Meal planning failed: {str(e)}"],
                "current_step": "error",
            }

    async def _plan_workout(self, state: FitnessState) -> Dict[str, Any]:
        """Generate workout plan"""
        try:
            user_id = state["user_id"]
            profile_dict = state.get("user_profile")

            if not profile_dict:
                raise ValueError("User profile not available for workout planning")

            profile = UserProfile(**profile_dict)
            workout_preferences = state.get("preferences", {}).get("workout_preferences", {})

            workout_request = WorkoutPlanRequest(
                user_id=user_id,
                split_type=workout_preferences.get("split_type", "full_body"),
                training_style=workout_preferences.get("training_style", "hypertrophy"),
                days_per_week=workout_preferences.get("days_per_week", profile.workout_frequency),
                duration_minutes=workout_preferences.get("duration_minutes", profile.workout_duration),
            )

            workout_plan = await self.workout_agent.generate_workout_plan(profile, workout_request)

            return {
                "workout_plan": workout_plan,
                "current_step": "workout_planned",
                "errors": [],
            }
        except Exception as e:
            logger.error(f"Error in workout planning: {str(e)}")
            return {
                "errors": [f"Workout planning failed: {str(e)}"],
                "current_step": "error",
            }

    async def _coordinate_plans(self, state: FitnessState) -> Dict[str, Any]:
        """Coordinate meal and workout plans"""
        try:
            meal_plan = state.get("meal_plan")
            workout_plan = state.get("workout_plan")
            profile_dict = state.get("user_profile")

            if not profile_dict:
                raise ValueError("User profile not available for plan coordination")

            profile = UserProfile(**profile_dict)

            # Use LLM to coordinate plans
            messages = [
                SystemMessage(
                    content="""You are a fitness coordinator who aligns meal and workout plans for optimal results.
                    
                    Analyze the meal and workout plans to ensure they work together synergistically.
                    Provide coordination advice on meal timing around workouts, nutrient timing, and overall plan alignment.
                    Focus on how nutrition supports training goals."""
                ),
                HumanMessage(
                    content=f"""Coordinate the following plans:
                    
                    User Goal: {profile.fitness_goal}
                    
                    Meal Plan: {meal_plan}
                    
                    Workout Plan: {workout_plan}
                    
                    Provide coordination advice and ensure both plans work together effectively."""
                ),
            ]

            coordination_advice = self.coordinator_llm.invoke(messages)

            return {
                "coordination_advice": coordination_advice,
                "current_step": "plans_coordinated",
                "errors": [],
            }
        except Exception as e:
            logger.error(f"Error in plan coordination: {str(e)}")
            return {
                "errors": [f"Plan coordination failed: {str(e)}"],
                "current_step": "error",
            }

    async def _generate_summary(self, state: FitnessState) -> Dict[str, Any]:
        """Generate comprehensive summary"""
        try:
            meal_plan = state.get("meal_plan")
            workout_plan = state.get("workout_plan")
            profile_dict = state.get("user_profile")

            if not profile_dict:
                raise ValueError("User profile not available for summary generation")

            profile = UserProfile(**profile_dict)

            # Only generate summary if we have at least one plan
            if meal_plan or workout_plan:
                summary = await self.summary_agent.create_summary(profile, meal_plan or {}, workout_plan or {})
            else:
                summary = "No plans generated to summarize."

            return {
                "summary": summary,
                "current_step": "summary_generated",
                "errors": [],
            }
        except Exception as e:
            logger.error(f"Error in summary generation: {str(e)}")
            return {
                "errors": [f"Summary generation failed: {str(e)}"],
                "current_step": "error",
            }

    async def run(self, request: LangGraphFitnessRequest) -> LangGraphFitnessResponse:
        """Run the fitness planning workflow"""
        try:
            # Initialize state
            initial_state: FitnessState = {
                "messages": [HumanMessage(content="Start fitness planning workflow")],
                "user_id": request.user_id,
                "user_profile": request.user_profile.model_dump() if request.user_profile else None,
                "meal_plan": None,
                "workout_plan": None,
                "summary": None,
                "current_step": "started",
                "errors": [],
                "preferences": {
                    "generate_meal_plan": request.generate_meal_plan,
                    "generate_workout_plan": request.generate_workout_plan,
                    "meal_preferences": request.meal_preferences,
                    "workout_preferences": request.workout_preferences,
                },
            }

            # Execute the workflow
            result = await self.workflow.ainvoke(initial_state)

            # Build response
            response = LangGraphFitnessResponse(
                user_id=request.user_id,
                workflow_status=result.get("current_step", "completed"),
                user_profile=result.get("user_profile"),
                meal_plan=result.get("meal_plan"),
                workout_plan=result.get("workout_plan"),
                summary=result.get("summary"),
                execution_steps=[
                    "profile_manager",
                    "meal_planner" if request.generate_meal_plan else "",
                    "workout_planner" if request.generate_workout_plan else "",
                    "plan_coordinator",
                    "summary_generator",
                ],
                errors=result.get("errors", []),
                generated_at=datetime.now(),
            )

            return response

        except Exception as e:
            logger.error(f"Error running workflow: {str(e)}")
            return LangGraphFitnessResponse(
                user_id=request.user_id,
                workflow_status="error",
                errors=[f"Workflow execution failed: {str(e)}"],
                generated_at=datetime.now(),
            )


@langgraph_agents.post("/langgraph-workflow/", response_model=LangGraphFitnessResponse)
async def run_fitness_workflow(request: LangGraphFitnessRequest):
    """Run the LangGraph fitness planning workflow"""
    try:
        workflow = FitnessWorkflow(
            use_o3_mini=request.use_o3_mini,
            use_full_database=request.use_full_database,
        )
        return await workflow.run(request)
    except Exception as e:
        logger.error(f"Error in workflow endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )