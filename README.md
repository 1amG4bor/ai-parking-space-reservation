# AI Parking Space Reservation 🚀

> **An AI ChatBot Application makes it easier to organize your trips. 🛫<br>
We help finding and reserving the right parking space for you.**
Our solution is not only booking a parking slot for you, but also helps you find the best parking space to park in. It provides you with an intuitive interface, detailed information, filter by your preferences, and more.<br>
With our application, you can easily book a parking spot with AI assistance. Our solution is based on natural language processing.

The goal of this project is to develop an intelligent chatbot with Retrieval-Augmented Generation (RAG) architecture.
The usecase is to help people find available and suitable parking spaces in the neighborhood of airports, cities, based on their preferences.

---
## Setup instructions - How to run? 🏃

> **Prerequisites**
> - Python 3.12 or higher
> - [UV - Python package manager](https://docs.astral.sh/uv/getting-started/installation/) installed
> - Docker is installed, enabled and running on your system

1. Clone this repository using: `git clone https:github.com/1amG4bor/ai-parking-space-reservation`
2. Go into the folder and do the initial setup _(create virtualenv, install dependencies)_ using: `uv sync`
3. Run the backend systems using: `uv run backend` or _'docker compose up -d'_
4. Run the chatbot using: `uv run app` or _'streamlit run app.py'_

💬: *"How can I help you today?"*

---
## Testing and Evaluation 📋

How to run tests and evaluation scipts?

- Run unit tests: `uv run unit_test`
- Evaluate model performance: `uv run performance_test` - *> TBD*
    *Note: the evaluation script will take a while to run, so please be patient. The evaluation results are saved in "evaluation" folder.*
- Evaluate chatbot accuracy: `uv run accuracy_test` - *> TBD*

---
## Architecture 🏗️

_The architecture contains the following components._

1. **Retrieval-Augmented Generation (RAG)** - This component uses a vector database to store and retrieve detailed information about parking spaces to assist in finding suitable parking spaces. The retrieval process is based on cosine similarity between the query and all available parking spaces.
2. **Vector Database** - A vector database stores the detailed information about parking spaces, including their location, price, and other relevant information.
3. **UI/Chatbot**  - The chatbot is a user interface that allows users to interact with the system by asking questions and receiving responses. The Chatbot is also used to book parking spaces and reserve them for a specific time period.
    - The UI is implemented with Streamlit and Python, to make an easy to setup environment for development and testing.
4. **Guardrails**  - Guardrails are designed to prevent exposure of sensitive data to the public.
5. **Evaluator**  - The evaluator is used to evaluate the performance of the chatbot. It provides a way to compare the performance of different versions of the chatbot and determine which version is most effective.
    - **Performance testing**: This involves running the chatbot on a variety of test cases and measuring the response time, accuracy, and other metrics. The goal is to determine how well the chatbot performs in different scenarios.
    - **Response accuracy measurement**: Measure the accuracy of the chatbot's responses by comparing them to a set of ground truth responses. This helps to ensure that the chatbot is able to provide accurate and relevant responses.

---
## Contributing 🤝

> **ℹ️ Contributions are always welcome, please open an issue or submit a pull request.**

### Utility scripts

- Running the linter: `uv run linter`
- Formatting the code: `uv run code_format`
- Running the unittests: `uv run unit_test`
- Running pre commit checks: `uv run pre_commit` _(includes formatting and linting the code and running unittests)_
- Start/Run the backend services: `uv run backend`
- Start/Run the frontend (Streamlit UI): `uv run app`

- Running the performance evaluation script: `uv run performance_test`
- Running the accuracy evaluation script: `uv run accuracy_test`

### Project structure

The folder `aspr` (ai-parking-space-reservation) contains the AI Chatengine in the following structure.

- `core`: Contains all core logic of the chatbot.
    - `agent`: holds the different agents that can be used in the processings and user interactions.
    - `storage`: contains the logic for storing static and synamic data.
    - `tools`: incorporates all tools needed in the ChatEngine




