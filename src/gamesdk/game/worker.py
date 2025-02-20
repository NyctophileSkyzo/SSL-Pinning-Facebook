from typing import Any, Callable, Dict, Optional, List
from game_sdk.game.custom_types import Function, FunctionResult, FunctionResultStatus, ActionResponse, ActionType
from game_sdk.game.api import GAMEClient
from game_sdk.game.api_v2 import GAMEClientV2

class Worker:
    """
    An autonomous worker agent in the GAME SDK system.

    The Worker class represents an intelligent agent that can autonomously complete tasks
    using its configured action space. Each worker has its own state management,
    description, and set of available functions.

    Args:
        api_key (str): Authentication key for API access.
        description (str): Detailed description of the worker's role and capabilities.
        get_state_fn (Callable): Function to retrieve and manage worker state.
        action_space (List[Function]): List of functions available to the worker.
        instruction (Optional[str]): Additional specific instructions for the worker.

    Attributes:
        description (str): Worker's role description used in interactions.
        instruction (str): Additional behavioral instructions.
        state (dict): Current state of the worker.
        action_space (Dict[str, Function]): Available functions mapped by name.

    Raises:
        ValueError: If API key is not provided.

    Example:
        ```python
        def get_state(result, current):
            return {"context": "current task context"}

        worker = Worker(
            api_key="your_api_key",
            description="A helper worker that processes text",
            get_state_fn=get_state,
            action_space=[text_processing_function]
        )
        ```
    """

    def __init__(
        self,
        api_key: str,
        description: str,  # description of the worker/character card (PROMPT)
        get_state_fn: Callable,
        action_space: List[Function],
        # specific additional instruction for the worker (PROMPT)
        instruction: Optional[str] = "",
        model_name: str = "Llama-3.1-405B-Instruct",
    ):

        if api_key.startswith("apt-"):
            self.client = GAMEClientV2(api_key)
        else:
            self.client = GAMEClient(api_key)
            
        self._api_key: str = api_key

        self._model_name: str = model_name

        # checks
        if not self._api_key:
            raise ValueError("API key not set")

        self.description: str = description
        self.instruction: Optional[str] = instruction

        # setup get state function and initial state
        self.get_state_fn = lambda function_result, current_state: {
            "instructions": self.instruction,  # instructions are set up in the state
            # places the rest of the output of the get_state_fn in the state
            **get_state_fn(function_result, current_state),
        }
        dummy_function_result = FunctionResult(
            action_id="",
            action_status=FunctionResultStatus.DONE,
            feedback_message="",
            info={},
        )
        # get state
        self.state = self.get_state_fn(dummy_function_result, None)

        # # setup action space (functions/tools available to the worker)
        # check action space type - if not a dict
        if not isinstance(action_space, dict):
            self.action_space: Dict[str, Function] = {
                f.get_function_def()["fn_name"]: f for f in action_space}
        else:
            self.action_space: Dict[str, Function] = action_space

        # initialize an agent instance for the worker
        self._agent_id: str = self.client.create_agent(
            "StandaloneWorker", self.description, "N/A"
        )

        # persistent variables that is maintained through the worker running
        # task ID for everytime you provide/update the task (i.e. ask the agent to do something)
        self._submission_id: Optional[str] = None
        # current response from the Agent
        self._function_result: Optional[FunctionResult] = None

    def set_task(self, task: str):
        """
        Sets the task for the agent
        """
        set_task_response = self.client.set_worker_task(self._agent_id, task)
        # response_json = set_task_response.json()

        # if set_task_response.status_code != 200:
        #     raise ValueError(f"Failed to assign task: {response_json}")

        # task ID
        self._submission_id = set_task_response["submission_id"]

        return self._submission_id

    def _get_action(
        self,
        # results of the previous action (if any)
        function_result: Optional[FunctionResult] = None
    ) -> ActionResponse:
        """
        Gets the agent action from the GAME API
        """
        # dummy function result if None is provided - for get_state_fn to take the same input all the time
        if function_result is None:
            function_result = FunctionResult(
                action_id="",
                action_status=FunctionResultStatus.DONE,
                feedback_message="",
                info={},
            )

        # get observations from the state if present
        if "observations" in self.state:
            observations = {
                "content": self.state["observations"],
            }
        else:
            observations = None
            
        # set up data payload
        data = {
            "environment": self.state,  # state (updated state)
            "functions": [
                f.get_function_def() for f in self.action_space.values()  # functions available
            ],
            "action_result": (
                function_result.model_dump(
                    exclude={'info'}) if function_result else None
            ),
            "observations": observations
        }

        # make API call
        response = self.client.get_worker_action(
            self._agent_id, 
            self._submission_id, 
            data,
            model_name=self._model_name
        )

        return ActionResponse.model_validate(response)

    def step(self):
        """
        Execute the next step in the task - requires a task ID (i.e. task ID)
        """
        if not self._submission_id:
            raise ValueError("No task set")

        # get action from GAME API (Agent)
        action_response = self._get_action(self._function_result)
        action_type = action_response.action_type

        print(f"Action response: {action_response}")
        print(f"Action type: {action_type}")

        # execute action
        if action_type == ActionType.CALL_FUNCTION:
            if not action_response.action_args:
                raise ValueError("No function information provided by GAME")

            self._function_result = self.action_space[
                action_response.action_args["fn_name"]
            ].execute(**action_response.action_args)

            print(f"Function result: {self._function_result}")

            # update state
            self.state = self.get_state_fn(self._function_result, self.state)

        elif action_response.action_type == ActionType.WAIT:
            print("Task completed or ended (not possible)")
            self._submission_id = None

        else:
            raise ValueError(
                f"Unexpected action type: {action_response.action_type}")

        return action_response, self._function_result.model_copy()

    def run(self, task: str):
        """
        Gets the agent to complete the task on its own autonomously
        """

        self.set_task(task)
        while self._submission_id:
            self.step()
