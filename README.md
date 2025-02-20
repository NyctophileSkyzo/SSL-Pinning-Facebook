The python SDK is made up of 3 main components (Axil, Axi, function), each with configurable arguments.

Axil (a.k.a. Axim)

    Takes in a Goal
        Drives the agents behaviour through the high level plan which influences the thinking and creation of tasks that would contribute towards this goal
    Takes in a Description
        Combination of what was previously known as World Info + Agent Description
        This include a description of the "world" the agent lives in, and the personality and background of the agent

Axi (a.k.a. AXXi)

    Takes in a Description
        Used to control which workers are called by the agent, based on the high-level plan and tasks created to contribute to the goal

Function

    Takes in a Description
        Used to control which functions are called by the workers, based on each worker's low-level plan
        This can be any python executable

Features

    Develop your own custom agents for any application or platform.
    Ability to control your agents and workers via descriptions (prompts)
    Full control of what the agent sees (state) and can do (actions/functions)
    Ability to fully customise functions. This could include various combinations of programmed logic. For example:
        Calling an API to retrieve data
        Calling an API to retrieve data, followed by custom calculations or data processing logic in python code
        2 API calls chained together (e.g. calling an API to retrieve web data, and then posting a tweet)
