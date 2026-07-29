# 🚀 Quick Start Guide - 3-Node Multi-Agent System

Get your multi-agent voice bot running in 5 minutes!

## ⚡ Prerequisites

```bash
# Python 3.8+
python --version

# Pip
pip --version
```

## 📦 Step 1: Install Dependencies

```bash
pip install pipecat-ai python-dotenv loguru openai
```

## 🔑 Step 2: Set Up API Keys

Create a `.env` file in the same directory as your bot files:

```bash
# Required API Keys
OPENAI_API_KEY=sk-your-openai-key-here
DEEPGRAM_API_KEY=your-deepgram-key-here
CARTESIA_API_KEY=your-cartesia-key-here
```

### Where to Get API Keys:

1. **OpenAI**: https://platform.openai.com/api-keys
2. **Deepgram**: https://console.deepgram.com/
3. **Cartesia**: https://cartesia.ai/

## 📁 Step 3: Organize Files

Make sure you have these files in your directory:

```
your-project/
├── .env                          # Your API keys
├── complete_3node_bot.py         # Main bot file
├── multi_node_orchestrator.py    # Core orchestrator
├── 3NODE_README.md               # Full documentation
└── test_3node_system.py          # Test suite (optional)
```

## 🧪 Step 4: Test the System (Optional)

Before running the full bot, test the components:

```bash
python test_3node_system.py
```

This will show you:
- ✅ Router node language detection
- ✅ English agent tool calling
- ✅ Spanish agent tool calling
- ✅ Complete flow simulation

## 🎯 Step 5: Run the Bot

```bash
python complete_3node_bot.py
```

You should see:

```
🚀 Starting 3-Node Multi-Agent Bot...
⏳ Loading models and imports (20 seconds, first run only)

[INFO] Loading Local Smart Turn Analyzer V3...
[INFO] ✅ Local Smart Turn Analyzer V3 loaded
[INFO] Loading Silero VAD model...
[INFO] ✅ Silero VAD model loaded
[INFO] ✅ All components loaded successfully!

======================================================================
Starting 3-Node Multi-Agent Bot
======================================================================
Architecture:
  1. Router Node - Detects language via OpenAI LLM
  2. English Agent Node - Handles English with tools
  3. Spanish Agent Node - Handles Spanish with tools
======================================================================

[INFO] ✅ STT initialized (Deepgram)
[INFO] ✅ TTS initialized (Cartesia)
[INFO] Creating Multi-Node Orchestrator...
...
```

## 🎤 Step 6: Start Talking!

Once connected, try these examples:

### English Queries:
- "What's the weather in New York?"
- "What time is it?"
- "Calculate 25 times 4"
- "Hello, how are you?"

### Spanish Queries:
- "¿Cómo está el clima en Madrid?"
- "¿Qué hora es?"
- "¿Cuánto es 15 más 8?"
- "Hola, ¿cómo estás?"

## 🔍 What Happens Behind the Scenes

### Example 1: "What's the weather in New York?"

```
You speak → STT → "What's the weather in New York?"
                    ↓
            Router Node detects: English
                    ↓
            Routes to: English Agent
                    ↓
            English Agent calls: get_weather(location="New York")
                    ↓
            Returns: "The weather in New York is 72°F and partly cloudy"
                    ↓
            TTS → You hear the response
```

### Example 2: "¿Qué hora es?"

```
You speak → STT → "¿Qué hora es?"
                    ↓
            Router Node detects: Spanish
                    ↓
            Routes to: Spanish Agent
                    ↓
            Spanish Agent calls: get_current_time()
                    ↓
            Returns: "Son las 14:30 horas"
                    ↓
            TTS → You hear the response
```

## 🎛️ System Architecture

```
┌─────────────────────────────────────────────┐
│           YOUR VOICE BOT PIPELINE           │
├─────────────────────────────────────────────┤
│                                             │
│  You speak → Microphone → STT → Orchestrator
│                                     ↓        │
│                            ┌────────────┐   │
│                            │   Router   │   │
│                            │    Node    │   │
│                            └──────┬─────┘   │
│                                   ↓         │
│                    ┌──────────────┴──────┐  │
│                    ↓                     ↓  │
│              ┌──────────┐          ┌────────┐
│              │ English  │          │Spanish │
│              │  Agent   │          │ Agent  │
│              └────┬─────┘          └───┬────┘
│                   └──────────┬─────────┘    │
│                              ↓              │
│                    Final Response → TTS     │
│                                     ↓       │
│                              You hear it    │
└─────────────────────────────────────────────┘
```

## 🛠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pipecat'"
**Solution**: Install dependencies
```bash
pip install pipecat-ai
```

### Issue: "OpenAI API key not found"
**Solution**: Check your `.env` file
```bash
cat .env  # Should show your API keys
```

### Issue: "Connection failed"
**Solution**: Check your API keys are valid
- Test OpenAI key: https://platform.openai.com/account/api-keys
- Test Deepgram key: https://console.deepgram.com/

### Issue: Bot not responding
**Solution**: Check the logs
```bash
# Look for errors in the console output
# Common issues:
# - Invalid API keys
# - Network connection
# - Microphone permissions
```

### Issue: Wrong language detection
**Solution**: The router uses keyword detection. You can:
1. Speak more clearly
2. Use more language-specific words
3. Adjust the router's system prompt

## 📊 Monitoring & Logs

The bot provides detailed logging. Watch for these key messages:

```
[ROUTER NODE] Processing query: ...        # Router receiving query
[ROUTER NODE] Tool call: route_to_agent    # Language detection complete
[ORCHESTRATOR] Routing to english_agent    # Routing decision
[ENGLISH AGENT] Executing tool: get_weather # Tool being called
[ORCHESTRATOR] Sending final response      # Response ready
```

## 🎯 Testing Individual Components

### Test 1: Router Only
```python
# In Python shell
from multi_node_orchestrator import RouterNode, NodeState

state = NodeState()
router = RouterNode(state)

# Test with different queries
await router.process_user_query("Hello", orchestrator)
await router.process_user_query("Hola", orchestrator)
```

### Test 2: English Agent Only
```python
from multi_node_orchestrator import EnglishAgentNode, NodeState

state = NodeState()
agent = EnglishAgentNode(state)

# Test with tool-requiring query
await agent.process_query("What's the weather?", orchestrator)
```

## 📈 Performance Tips

1. **First Run**: Takes ~20 seconds to load models
2. **Subsequent Runs**: Models cached, starts faster
3. **Response Time**: 
   - Simple queries: 1-2 seconds
   - Tool-requiring queries: 2-4 seconds
   - Complex multi-tool queries: 4-6 seconds

## 🔐 Security Notes

- ✅ API keys in `.env` file (not in code)
- ✅ `.env` should be in `.gitignore`
- ✅ Never commit API keys to version control
- ✅ Use environment-specific keys (dev/prod)

## 📚 Next Steps

Once your bot is running:

1. **Customize Tools**: Add more tools to agents
2. **Add Languages**: Create French, German agents
3. **Enhance Router**: Improve language detection
4. **Add RAG**: Integrate Qdrant for knowledge base
5. **Deploy**: Move to production environment

## 🎓 Learning Resources

- **Full Documentation**: See `3NODE_README.md`
- **Test Suite**: Run `test_3node_system.py`
- **Pipecat Docs**: https://docs.pipecat.ai/
- **OpenAI Function Calling**: https://platform.openai.com/docs/guides/function-calling

## ✅ Success Checklist

- [ ] Dependencies installed
- [ ] API keys configured
- [ ] Files in correct location
- [ ] Test suite runs successfully
- [ ] Bot starts without errors
- [ ] Can detect English
- [ ] Can detect Spanish
- [ ] Tools work correctly
- [ ] Responses in correct language

## 🎉 You're Ready!

Your 3-node multi-agent voice bot is now running! 

Try saying:
- **English**: "What's the weather in London?"
- **Spanish**: "¿Qué hora es en España?"

The bot will automatically detect the language and respond appropriately!

---

**Need Help?** Check the full documentation in `3NODE_README.md` or review the test output from `test_3node_system.py`.

**Happy Building! 🚀**
