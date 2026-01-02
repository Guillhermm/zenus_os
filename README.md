# Zenus OS

Zenus OS is a voice-first, AI-mediated operating system layer that replaces traditional user interfaces with intent-based interaction and bounded autonomy.

This is, a full operating systems that can be controlled by voice, where AI:

- Understands complex user intent.
- Plans and performs operations autonomously.
- Interacts with system APIs to get things done.
- Can talk back, ask clarifying questions, and learn from user behavior.

Although there are research prototypes already in place, still there is no full voice controlled OS consumer-ready for end users. With this project, we aim to create voice-first AI assisted OS that is not just reactive, but autonomous, context aware, and capable of executing complex tasks based on natural language instructions.

What would be the impacts on user experience? Should we build a new concept of user interface, or the new concept is totally user customizable?

Discussions over possible impacts and needed technology and scientific improvements can be found **[here](./docs/advances.md)**.

## 1. Prototype

### 1.1. System Architecture

#### 1.1.1. AI Assistant Layer

- LLM (Large Language Model) that interprets intent.
- Is there another better way than LLM, more efficient that does not consume much from CPU, for the system core?
- Options to consider are GPT, Mistral, LLaMa (local or cloud?).
- Autonomous agent capabilities?
- Maybe we can build this as a modular backend that sits between voice and the system APIs?

#### 1.1.2. Voice Interface Layer

- Voice-to-text: Whisper (local), Deepgram, or Google SST.
- Text-to-voice: ElevenLabs, Piper, or built-in TTS engines.

Natural conversion loop:

```
Wake word → voice capture → intent → action → AI response → spoken feedback
```

#### 1.1.3. OS Shell/Control Layer

This layer connects AI actions to real system commands.

**Options:**

- Build a custom Linux distro with voice + AI shell (desirable by the end of the prototype).
- Overlay it on existing OS (like a custom desktop environment).
- Use an existing OS but control it fully via APIs/scripts

Would we be able to fully control OS in second and third approaches?

#### 1.1.4. Autonomous Task Engine

AI should not just follow single commands, it should:

- Decompose tasks.
- Ask for clarification when needed.
- Execute subtasks step by step.
- Adapt to errors or unexpected results.

#### 1.1.5. Security and Permissions

A voice controlled OS must have strong authentication, especially for destructive actions.

**Options:**

- Voice ID or wake word auth.
- Role-based task restrictions.
- Confirmation layers for sensitive operations.

We should be able to "translate" voice into a single id, combined with passphrase, for authentication. Passwords might be fallback. Instead of wake word, OS might recognize user voice timbre.

## 2. Use Case Scenarios Examples

### 2.1. Daily Tasks

"Check my calendar and tell me what's coming up"

"Organize my downloads by file type and delete duplicates"

"Summarize latest posts from my social media"

### 2.2. Autonomous Ops

"Find the 5 largest files on my system, back them up, and free up space"

"Setup a new dev environment with Python, Docker, and VS Code"

### 2.3. Developer Mode

"Create a Python script that monitors CPU usage and logs"

"Download latest stable release of MySQL and configure it"

## Setup

Make it sure `python3` and `python3-venv` are installed:

```bash
sudo apt update
sudo apt install python3 python3-venv
```

Create a **virtual environment** on the project root and activate it (needed for every time):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt # Dev env only
```

## Run

On root, run:

```bash
python3 src/main.py

# That will initialize Zenus OS CLI, so you can provide commands
zenus > Organize my Downloads folder by file type, do not delete anything
```