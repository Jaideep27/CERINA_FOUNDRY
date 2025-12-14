# CERINA

AI-Powered CBT Protocol Generator featuring multi-agent collaboration, quality assurance, and safety validation.

## 🌟 Features

- **Multi-Agent Orchestration**: Specialized AI agents (Filter, Drafter, Safety, Critic) collaborate to create high-quality protocols
- **Bidirectional Communication**: Agents iterate with each other to improve quality (Critic↔Drafter, Critic↔Safety loops)
- **Human-in-the-Loop**: Requires human approval before finalizing protocols
- **Safety Validation**: Dual safety checks ensure appropriate therapeutic content
- **Quality Assurance**: Strict grading criteria with iterative improvements
- **Markdown Formatting**: Beautiful, readable protocol output
- **Auto-Save**: Approved protocols saved to `CBT_Downloaded/` folder
- **Resume Capability**: Continue interrupted workflows from checkpoints
- **MCP Server**: Accessible via Claude Desktop or any MCP client
- **Multiple Interfaces**: Web UI, Terminal client, or MCP integration

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Jaideep27/CERINA_FOUNDRY.git
   cd CERINA_FOUNDRY
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Create `.env` file**
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

**Option 1: Web Interface**

1. **Start Backend**
   ```bash
   cd CERINA_FOUNDRY
   start_backend.bat
   ```

2. **Start Frontend**
   ```bash
   cd CERINA_FOUNDRY
   start_frontend.bat
   ```

3. **Open Browser**
   Navigate to `http://localhost:5174`

**Option 2: MCP Client (Claude Desktop)**

CERINA can be used as an MCP server with Claude Desktop as the client:

1. **Add to Claude Desktop Config**
   
   Open `%APPDATA%\Claude\claude_desktop_config.json` and add:
   
   ```json
   {
     "mcpServers": {
       "cerina-foundry": {
         "command": "C:/Cerina_Foundry_ver0/backend/venv/Scripts/python.exe",
         "args": [
           "C:/Cerina_Foundry_ver0/backend/mcp_server.py",
           "--transport",
           "stdio"
         ],
         "env": {
           "PYTHONPATH": "C:/Cerina_Foundry_ver0",
           "PYTHONUNBUFFERED": "1"
         }
       }
     }
   }
   ```

2. **Restart Claude Desktop**

3. **Use the tool**
   Ask Claude: *"Create a CBT protocol for sleep anxiety"*
   
   Claude will call the `create_protocol` MCP tool and return the generated protocol.

**Option 3: Terminal Client**

```bash
python run_client.py "CBT for test anxiety"
```

## 📖 Usage

1. Enter a CBT-related query (e.g., "CBT for sleep anxiety")
2. Click "Start Foundry"
3. Watch agents collaborate in real-time
4. Review the generated protocol
5. Click "Approve & Finalize" to save
6. Find saved protocols in `CBT_Downloaded/`

## 🏗️ Architecture

```
Filter Agent → Drafter Agent → Safety Agent → Critic Agent → Human Approval
     ↓              ↕                ↕              ↕
  Rejection    (Iterations)    (Consults)    (Revisions)
```

**Agent Roles:**
- **Filter**: Validates query relevance and detects PII
- **Drafter**: Creates initial CBT protocol drafts and revisions
- **Safety**: Reviews for safety concerns and appropriateness
- **Critic**: Evaluates quality with strict grading standards
- **Interrupt**: Pauses for human approval

## 🔄 Bidirectional Workflows

Agents can iterate to improve quality:
- **Critic ↔ Drafter**: Up to 2 iterations for quality improvement
- **Critic ↔ Safety**: Up to 2 consultations on safety concerns
- **Filter ↔ Safety**: Up to 2 iterations for input validation

## 🛠️ Tech Stack

**Backend:**
- Python, FastAPI
- LangGraph, LangChain
- OpenAI GPT-4o-mini
- LangGraph Checkpointing (MemorySaver)

**Frontend:**
- React, TypeScript
- Vite
- TailwindCSS
- ReactMarkdown

## 📂 Project Structure

```
CERINA_FOUNDRY/
├── backend/
│   ├── agents/          # AI agent implementations
│   ├── server.py        # FastAPI server with SSE
│   ├── graph.py         # LangGraph workflow definition
│   ├── state.py         # Shared state schema
│   └── database.py      # Checkpointing configuration
├── frontend/
│   └── src/
│       ├── components/  # React components
│       └── App.tsx      # Main application
├── CBT_Downloaded/      # Saved protocols
└── run_client.py        # Terminal client (optional)
```

## 🎯 Example Output

Protocols are formatted in clean Markdown:

```markdown
# CBT Protocol: Managing Test Anxiety

## Understanding the Issue
[Empathetic validation...]

## CBT Technique: Cognitive Restructuring
[Technique explanation...]

## Step-by-Step Exercise
### Step 1: Identify Anxious Thoughts
- **Action:** Write down worried thoughts
- **Example:** "I will fail this exam"
...
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 👨‍💻 Author

**Jaideep**
- GitHub: [@Jaideep27](https://github.com/Jaideep27)

## 🙏 Acknowledgments

- LangGraph for agent orchestration
- OpenAI for language models
- FastAPI for backend framework

---

**Note**: This is a demonstration project. For production mental health applications, consult licensed mental health professionals.
