from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel, Field
from typing import List
from crewai_tools import SerperDevTool
from crewai import LLM
from .tools.push_tool import PushNotificationTool
import os
from dotenv import load_dotenv
load_dotenv()

llm = LLM(
    model="gemini-3.5-flash-lite",
    base_url="https://api.mixroute.ai/v1",
    api_key=os.getenv("MIXROUTE_API_KEY")
)

llm1 = LLM(
    model="deepseek-v4-flash",
    base_url="https://api.mixroute.ai/v1",
    api_key=os.getenv("MIXROUTE_API_KEY")
)

class TrendingCompany(BaseModel):
    """ A company that is in the news and attracting attention """
    name: str = Field(description="Company name")
    ticket: str = Field(description="Stock ticker symbol")
    reason: str = Field(description="Reason this company is trending in the news")

# class TrendingCompanyList(BaseModel):
#     """ List of multiple trending companies that are in the news """
#     companies: List[TrendingCompany] = Field(description="List of companies trending in the news")

class TrendingCompanyResearch(BaseModel):
    """Detailed research on a company"""
    name: str = Field(description="Company name")
    market_position: str = Field(description="Current market position and competitive analysis")
    future_outlook: str = Field(description="Future outlook and growth prospects")
    investment_potential: str = Field(description="Investment potential and suitability for investment")

# class TrendingCompanyResearchList(BaseModel):
#     """ List of research reports on trending companies """
#     companies: List[TrendingCompanyResearch] = Field(description="Comprehensive research on all trending companies")

class TrendingCompanyList(BaseModel):
    companies: List[dict] = Field(
        description=(
            "List of companies. Each company must contain "
            "name, ticket, and reason."
        )
    )

class TrendingCompanyResearchList(BaseModel):
    companies: List[dict] = Field(
        description=(
            "List of research reports. Each report must contain "
            "name, market_position, future_outlook, and "
            "investment_potential."
        )
    )

@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def trending_company_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['trending_company_finder'],
            llm = llm1,
            tools = [SerperDevTool()],
            verbose=True
        )

    @agent
    def financial_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_researcher'],
            llm = llm1,
            tools = [SerperDevTool()],
            verbose=True
        )
    
    @agent
    def stock_picker(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_picker'],
            llm = llm1,
            tools = [PushNotificationTool()],
            verbose=True
        )
    
    @task
    def find_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_companies'],
            output_pydantic=TrendingCompanyList
        )

    @task
    def research_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['research_trending_companies'],
            output_pydantic=TrendingCompanyResearchList
        )

    @task
    def pick_best_company(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_company'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the StockPicker crew"""

        manager = Agent(
            config=self.agents_config['manager'],
            llm = llm,
            allow_delegation=True,
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks, 
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            memory=False,
            embedder={
                "provider": "openai",
                "config": {
                    "api_key": os.getenv("OPENROUTER_API_KEY"),
                    "api_base": "https://openrouter.ai/api/v1",
                    "model_name": "nvidia/llama-nemotron-embed-vl-1b-v2:free",
                },
            },
        )
