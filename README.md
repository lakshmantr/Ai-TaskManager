AI Voice Task Manager

A fully voice-controlled task manager powered by FastAPI, WebSockets, SQLAlchemy, Redis, Groq Llama-3.3, SarvamAI Speech-to-Text, and ElevenLabs Text-to-Speech. You speak, and the system understands, processes, stores tasks, and talks back to you.

Features

Voice Input (SarvamAI STT): Records audio from the microphone and converts speech to text using SarvamAI’s Saarika v2.5 model.

Intent Extraction (Groq Llama-3.3): Extracts intent based on voice commands such as adding a task, updating a task, deleting a task, getting all tasks, getting a specific task, filtering tasks by time/status/description, getting the next pending task, stopping the assistant, or handling unknown commands.

Real-Time WebSocket Backend (FastAPI): Uses a WebSocket endpoint (/ws) to communicate with the voice client instantly with no delay.

Database Storage (SQLAlchemy ORM): Stores each task with its name, time, description, and status (pending or completed).

Redis Caching: Frequently accessed tasks are cached to improve speed.

Text-to-Speech Output (ElevenLabs): Converts the assistant’s responses into real-time speech.

Modular Architecture: Separates STT, LLM logic, TTS, database models, WebSocket logic, and response generation for clean maintainability.

Project Structure

The project contains the following main files: _models.py for the SQLAlchemy task model, database.py for the DB engine and session, llm.py for the voice/LLM/WebSocket client loop, main.py for FastAPI’s WebSocket backend, response.py for natural responses, stt.py for SarvamAI speech-to-text, and tts.py for ElevenLabs speech output.

Environment Setup

Clone the repository using git clone <https://github.com/lakshmantr/Ai-TaskManager.git>.

Create a virtual environment using python -m venv venv, then activate it using venv\Scripts\activate (Windows) or source venv/bin/activate (macOS/Linux).
Check the comments in stt.py 

Install dependencies using pip install -r requirements.txt.

Create a .env file in the project root and add the following values:
DATABASE_URL=sqlite:///tasks.db
GROQ_API_KEY=your_groq_key
SARVAM_API_KEY=your_sarvam_key
ELEVENLABS_API_KEY=your_eleven_key

Start the FastAPI backend using uvicorn main:app --ws-ping-timeout 20 --ws-ping-interval 120
The WebSocket endpoint will be available at ws://127.0.0.1:8000/ws

Run the LLM + voice client using python llm.py.

Example Voice Commands

Add a task called buy groceries at 6 pm
Update the task gym to completed
Delete the task homework
What are my pending tasks
Tell me the next task
Stop

Tech Stack

Speech-to-Text: SarvamAI
Text-to-Speech: ElevenLabs
LLM: Groq Llama-3.3-70B
Backend: FastAPI + WebSockets
Cache: Redis
Database: SQLAlchemy ORM
Language: Python