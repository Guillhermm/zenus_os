"""
Multi-Agent Collaboration System

Specialized agents work together to solve complex tasks:
- Researcher: Gathers information and finds solutions
- Planner: Creates detailed execution plans
- Executor: Implements the plan
- Validator: Verifies results and quality

This is true AI collaboration - not just sub-processes!
"""

import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime


class AgentRole(Enum):
    """Specialized agent roles"""
    RESEARCHER = "researcher"  # Gathers info, finds solutions
    PLANNER = "planner"        # Creates detailed plans
    EXECUTOR = "executor"      # Implements solutions
    VALIDATOR = "validator"    # Verifies results
    COORDINATOR = "coordinator"  # Orchestrates collaboration


@dataclass
class Message:
    """Inter-agent communication message"""
    from_agent: AgentRole
    to_agent: AgentRole
    message_type: str  # "request", "response", "update", "question"
    content: Dict
    timestamp: str
    message_id: str
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['from_agent'] = self.from_agent.value
        result['to_agent'] = self.to_agent.value
        return result


@dataclass
class AgentResult:
    """Result from an agent's work"""
    agent: AgentRole
    success: bool
    output: Dict
    confidence: float  # 0.0 to 1.0
    reasoning: str
    duration: float
    messages_sent: int
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['agent'] = self.agent.value
        return result


@dataclass
class CollaborationSession:
    """A multi-agent collaboration session"""
    session_id: str
    task: str
    agents_involved: List[AgentRole]
    messages: List[Message]
    results: List[AgentResult]
    final_result: Optional[str]
    success: bool
    total_duration: float
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['agents_involved'] = [a.value for a in self.agents_involved]
        result['messages'] = [m.to_dict() for m in self.messages]
        result['results'] = [r.to_dict() for r in self.results]
        return result


class Agent:
    """Base class for specialized agents"""
    
    def __init__(self, role: AgentRole, llm, logger):
        self.role = role
        self.llm = llm
        self.logger = logger
        self.messages_sent = 0
        self.messages_received = 0
    
    def execute(self, task: str, context: Dict) -> AgentResult:
        """Execute agent-specific task"""
        raise NotImplementedError("Subclasses must implement execute()")
    
    def send_message(
        self, 
        to_agent: AgentRole, 
        message_type: str, 
        content: Dict,
        session: CollaborationSession
    ) -> Message:
        """Send message to another agent"""
        import uuid
        
        msg = Message(
            from_agent=self.role,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            message_id=str(uuid.uuid4())[:8]
        )
        
        session.messages.append(msg)
        self.messages_sent += 1
        
        return msg
    
    def _build_prompt(self, task: str, context: Dict) -> str:
        """Build role-specific prompt"""
        raise NotImplementedError("Subclasses must implement _build_prompt()")


class ResearcherAgent(Agent):
    """Gathers information and finds potential solutions"""
    
    def __init__(self, llm, logger):
        super().__init__(AgentRole.RESEARCHER, llm, logger)
    
    def execute(self, task: str, context: Dict) -> AgentResult:
        """Research the problem and find solutions"""
        import time
        start_time = time.time()
        
        prompt = self._build_prompt(task, context)
        
        try:
            response = self.llm.generate(prompt, stream=True)
            research_data = json.loads(response)
            
            result = AgentResult(
                agent=self.role,
                success=True,
                output=research_data,
                confidence=research_data.get("confidence", 0.8),
                reasoning=research_data.get("reasoning", "Research completed"),
                duration=time.time() - start_time,
                messages_sent=self.messages_sent
            )
            
            return result
            
        except Exception as e:
            return AgentResult(
                agent=self.role,
                success=False,
                output={"error": str(e)},
                confidence=0.0,
                reasoning=f"Research failed: {e}",
                duration=time.time() - start_time,
                messages_sent=self.messages_sent
            )
    
    def _build_prompt(self, task: str, context: Dict) -> str:
        return f"""You are a Research Agent. Your job is to gather information and find potential solutions.

Task: {task}

Context: {json.dumps(context, indent=2)}

Research thoroughly and provide:
1. Problem analysis
2. Available approaches (3-5 options)
3. Recommended tools/technologies
4. Potential challenges
5. Best practices
6. Resources/documentation links

Return JSON:
{{
  "analysis": "Problem breakdown",
  "approaches": [
    {{"name": "Approach 1", "pros": [], "cons": [], "complexity": "low/medium/high"}},
    ...
  ],
  "recommended_tools": ["tool1", "tool2"],
  "challenges": ["challenge1", "challenge2"],
  "best_practices": ["practice1", "practice2"],
  "confidence": 0.85,
  "reasoning": "Why this research is solid"
}}"""


class PlannerAgent(Agent):
    """Creates detailed execution plans"""
    
    def __init__(self, llm, logger):
        super().__init__(AgentRole.PLANNER, llm, logger)
    
    def execute(self, task: str, context: Dict) -> AgentResult:
        """Create detailed execution plan"""
        import time
        start_time = time.time()
        
        prompt = self._build_prompt(task, context)
        
        try:
            response = self.llm.generate(prompt, stream=True)
            plan_data = json.loads(response)
            
            result = AgentResult(
                agent=self.role,
                success=True,
                output=plan_data,
                confidence=plan_data.get("confidence", 0.8),
                reasoning=plan_data.get("reasoning", "Plan created"),
                duration=time.time() - start_time,
                messages_sent=self.messages_sent
            )
            
            return result
            
        except Exception as e:
            return AgentResult(
                agent=self.role,
                success=False,
                output={"error": str(e)},
                confidence=0.0,
                reasoning=f"Planning failed: {e}",
                duration=time.time() - start_time,
                messages_sent=self.messages_sent
            )
    
    def _build_prompt(self, task: str, context: Dict) -> str:
        research_output = context.get("research", {})
        
        return f"""You are a Planning Agent. Create a detailed, step-by-step execution plan.

Task: {task}

Research Results: {json.dumps(research_output, indent=2)}

Create a detailed plan with:
1. Prerequisites check
2. Ordered steps (with dependencies)
3. Risk assessment per step
4. Rollback strategies
5. Validation checkpoints
6. Estimated timeline

Return JSON:
{{
  "prerequisites": ["prereq1", "prereq2"],
  "steps": [
    {{
      "step_num": 1,
      "action": "What to do",
      "command": "Specific command",
      "risk": "low/medium/high",
      "depends_on": [],
      "validation": "How to verify",
      "rollback": "How to undo"
    }},
    ...
  ],
  "timeline": "Estimated time",
  "risks": [{{"risk": "What could go wrong", "mitigation": "How to prevent"}}],
  "confidence": 0.85,
  "reasoning": "Why this plan will work"
}}"""


class ExecutorAgent(Agent):
    """Implements the plan"""
    
    def __init__(self, llm, logger, orchestrator):
        super().__init__(AgentRole.EXECUTOR, llm, logger)
        self.orchestrator = orchestrator
    
    def execute(self, task: str, context: Dict) -> AgentResult:
        """Execute the plan"""
        import time
        start_time = time.time()
        
        plan = context.get("plan", {})
        steps = plan.get("steps", [])
        
        results = []
        all_success = True
        
        for step in steps:
            try:
                # Execute step using orchestrator
                command = step.get("command", step.get("action"))
                result = self.orchestrator.execute_command(command)
                
                results.append({
                    "step": step.get("step_num"),
                    "action": step.get("action"),
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "step": step.get("step_num"),
                    "action": step.get("action"),
                    "success": False,
                    "error": str(e)
                })
                all_success = False
                
                # Check if we should continue or stop
                if step.get("risk") == "high":
                    break  # Stop on high-risk failure
        
        return AgentResult(
            agent=self.role,
            success=all_success,
            output={"results": results},
            confidence=1.0 if all_success else 0.5,
            reasoning=f"Executed {len(results)} steps, {sum(r['success'] for r in results)} succeeded",
            duration=time.time() - start_time,
            messages_sent=self.messages_sent
        )
    
    def _build_prompt(self, task: str, context: Dict) -> str:
        # Executor doesn't need LLM prompts - it uses orchestrator directly
        return ""


class ValidatorAgent(Agent):
    """Verifies results and ensures quality"""
    
    def __init__(self, llm, logger):
        super().__init__(AgentRole.VALIDATOR, llm, logger)
    
    def execute(self, task: str, context: Dict) -> AgentResult:
        """Validate execution results"""
        import time
        start_time = time.time()
        
        prompt = self._build_prompt(task, context)
        
        try:
            response = self.llm.generate(prompt, stream=True)
            validation_data = json.loads(response)
            
            result = AgentResult(
                agent=self.role,
                success=validation_data.get("overall_success", True),
                output=validation_data,
                confidence=validation_data.get("confidence", 0.8),
                reasoning=validation_data.get("reasoning", "Validation complete"),
                duration=time.time() - start_time,
                messages_sent=self.messages_sent
            )
            
            return result
            
        except Exception as e:
            return AgentResult(
                agent=self.role,
                success=False,
                output={"error": str(e)},
                confidence=0.0,
                reasoning=f"Validation failed: {e}",
                duration=time.time() - start_time,
                messages_sent=self.messages_sent
            )
    
    def _build_prompt(self, task: str, context: Dict) -> str:
        plan = context.get("plan", {})
        execution_results = context.get("execution", {})
        
        return f"""You are a Validator Agent. Verify that the execution met requirements.

Original Task: {task}

Plan: {json.dumps(plan, indent=2)}

Execution Results: {json.dumps(execution_results, indent=2)}

Validate:
1. All steps completed successfully
2. Results match expectations
3. No errors or warnings
4. Quality standards met
5. Side effects acceptable

Return JSON:
{{
  "overall_success": true/false,
  "checks": [
    {{"check": "What was verified", "passed": true/false, "details": "Details"}},
    ...
  ],
  "issues": ["issue1", "issue2"],
  "recommendations": ["recommendation1"],
  "confidence": 0.9,
  "reasoning": "Why validation passed/failed"
}}"""


class MultiAgentSystem:
    """Coordinates multiple agents to solve complex tasks"""
    
    def __init__(self, llm, logger, orchestrator=None):
        self.llm = llm
        self.logger = logger
        self.orchestrator = orchestrator
        
        # Initialize agents
        self.researcher = ResearcherAgent(llm, logger)
        self.planner = PlannerAgent(llm, logger)
        self.executor = ExecutorAgent(llm, logger, orchestrator) if orchestrator else None
        self.validator = ValidatorAgent(llm, logger)
    
    def collaborate(self, task: str, context: Dict = None) -> CollaborationSession:
        """
        Run multi-agent collaboration to solve task
        
        Workflow:
        1. Researcher gathers information
        2. Planner creates execution plan
        3. Executor implements plan
        4. Validator verifies results
        """
        import time
        import uuid
        
        start_time = time.time()
        context = context or {}
        
        session = CollaborationSession(
            session_id=str(uuid.uuid4())[:8],
            task=task,
            agents_involved=[],
            messages=[],
            results=[],
            final_result=None,
            success=False,
            total_duration=0.0
        )
        
        try:
            # Phase 1: Research
            self.logger.log_info("multi_agent_research", {"task": task})
            session.agents_involved.append(AgentRole.RESEARCHER)
            
            research_result = self.researcher.execute(task, context)
            session.results.append(research_result)
            
            if not research_result.success:
                session.final_result = "Research failed"
                session.success = False
                session.total_duration = time.time() - start_time
                return session
            
            context['research'] = research_result.output
            
            # Phase 2: Planning
            self.logger.log_info("multi_agent_planning", {"task": task})
            session.agents_involved.append(AgentRole.PLANNER)
            
            planning_result = self.planner.execute(task, context)
            session.results.append(planning_result)
            
            if not planning_result.success:
                session.final_result = "Planning failed"
                session.success = False
                session.total_duration = time.time() - start_time
                return session
            
            context['plan'] = planning_result.output
            
            # Phase 3: Execution (if executor available)
            if self.executor:
                self.logger.log_info("multi_agent_execution", {"task": task})
                session.agents_involved.append(AgentRole.EXECUTOR)
                
                execution_result = self.executor.execute(task, context)
                session.results.append(execution_result)
                
                if not execution_result.success:
                    session.final_result = "Execution failed"
                    session.success = False
                    session.total_duration = time.time() - start_time
                    return session
                
                context['execution'] = execution_result.output
            
            # Phase 4: Validation
            self.logger.log_info("multi_agent_validation", {"task": task})
            session.agents_involved.append(AgentRole.VALIDATOR)
            
            validation_result = self.validator.execute(task, context)
            session.results.append(validation_result)
            
            session.success = validation_result.success
            session.final_result = validation_result.output.get("reasoning", "Completed")
            session.total_duration = time.time() - start_time
            
            # Log session summary
            self.logger.log_info("multi_agent_complete", session.to_dict())
            
            return session
            
        except Exception as e:
            session.final_result = f"Collaboration failed: {e}"
            session.success = False
            session.total_duration = time.time() - start_time
            self.logger.log_error(f"Multi-agent collaboration failed: {e}")
            return session


# Singleton instance
_multi_agent_system = None


def get_multi_agent_system(llm, logger, orchestrator=None) -> MultiAgentSystem:
    """Get or create multi-agent system"""
    global _multi_agent_system
    if _multi_agent_system is None:
        _multi_agent_system = MultiAgentSystem(llm, logger, orchestrator)
    return _multi_agent_system
