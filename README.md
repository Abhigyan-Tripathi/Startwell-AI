# StartWell AI: Wellness Planner & SMART Goal Assistant

StartWell is a professional AI assistant designed to help individuals track daily habits, generate SMART wellness goals, plan actionable tasks, and monitor progress over time using a data-driven approach.

## Features

- **Daily Logging**: Record exercise hours, sleep duration, productivity time, and self-help activities through an intuitive interface.
- **SMART Goal Generation**: Automatically create personalized SMART (Specific, Measurable, Achievable, Relevant, Time-bound) goals via a language model API.
- **Task Planning**: Break down weekly goals into actionable daily tasks and store them in a relational database.
- **Progress Tracking**: Display a weekly log and calendar view of completed and pending tasks for clear visualization.
- **Weekly Feedback**: Provide context-aware advice based on user data and task completion metrics.

## Technology Stack

- **Streamlit**: Front-end framework for building interactive web interfaces.  
- **Hugging Face Inference API**: Remote language model inference for goal and advice generation.
- **Chroma DB**: For retrieval of user logs as context to llms.
- **SQLite**: Lightweight relational database for persisting daily logs and task status.  
- **Requests**: HTTP client library to interact with the inference API.  
- **python-dotenv**: Environment variable management for secure configuration.

## Installation and Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smartwell-agent.git](https://github.com/Abhigyan-Tripathi/Startwell-AI.git
   cd startwell-agent
   ```
2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate       # macOS/Linux
   venv\Scripts\activate.bat    # Windows
   ```
3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Configure environment variables**
   - Copy `.env.example` to `.env`.
   - Set your Hugging Face API token in the `.env` file:
     ```dotenv
     HF_API_TOKEN=your_hf_api_token_here
     ```
5. **Run the application**
   ```bash
   streamlit run main.py
   ```

## Contribution Guidelines

Contributions are welcome. To propose changes:

1. Fork the repository.  
2. Create a feature branch.  
3. Commit your changes with clear messages.  
4. Submit a pull request for review.

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.

---

For questions or assistance, please open an issue or contact the maintainers.
