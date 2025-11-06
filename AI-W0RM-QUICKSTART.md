# AI-W0rM Quick Start Guide

## ⚠️ AUTHORIZATION REQUIRED - READ THIS FIRST ⚠️

**STOP**: Do you have written authorization to test the target system?
- ✅ YES → Proceed with testing
- ❌ NO → DO NOT USE THIS TOOL (it's illegal)

---

## Quick Setup

### 1. Start Mastra Server

```bash
npm run dev
```

### 2. Set Up Test Environment (Optional)

For safe testing in an isolated lab:

```bash
# Terminal 1: Start vulnerable Ray server
docker pull rayproject/ray:2.6.3
docker run --shm-size=512M -it -p 8265:8265 rayproject/ray:2.6.3
# Inside container:
ray start --head --dashboard-host=0.0.0.0
```

---

## Quick Commands

### Check if Target is Vulnerable

Use the `checkRayVulnerability` tool:

```json
{
  "targetHost": "localhost",
  "targetPort": 8265
}
```

### Execute Command (AUTHORIZED ONLY)

Use the `aiW0rmTool`:

```json
{
  "targetHost": "localhost",
  "targetPort": 8265,
  "command": "echo 'Hello from AI-W0rM'"
}
```

---

## Common Test Commands

### Safe Reconnaissance Commands

```bash
# Check current user
"whoami"

# Check hostname
"hostname"

# Check OS version
"uname -a"

# List current directory
"ls -la"

# Check environment variables
"env"
```

### Network Commands

```bash
# Check network interfaces
"ip addr"

# Check listening ports
"netstat -tuln"

# Check DNS resolution
"nslookup google.com"
```

---

## Remediation Quick Reference

### For Administrators

1. **Immediate Actions**:
   ```bash
   # Stop Ray if unauthorized
   ray stop
   
   # Block port 8265
   sudo ufw deny 8265
   ```

2. **Secure Configuration**:
   - Enable authentication
   - Restrict network access
   - Update to latest Ray version
   - Monitor job submissions

3. **Detection**:
   ```bash
   # Check Ray logs
   tail -f /tmp/ray/session_*/logs/dashboard.log
   
   # Check for suspicious jobs
   ray list jobs
   ```

---

## Troubleshooting

### Connection Refused
- Check if Ray is running: `curl http://target:8265`
- Verify port is correct (default: 8265)
- Check firewall rules

### Timeout
- Increase timeout parameter
- Check network connectivity
- Verify target is reachable

### Command Not Executing
- Check Ray logs for errors
- Verify command syntax
- Try simpler commands first

---

## Important Reminders

1. ✅ **Always get authorization**
2. 📝 **Document everything**
3. 🔒 **Test in isolated environments**
4. 🚫 **Never use on production without approval**
5. 📊 **Report findings responsibly**

---

## Need Help?

- Read full documentation: `AI-W0RM-README.md`
- Check tool implementation: `src/mastra/tools/ai-w0rm-tool.ts`
- Review agent code: `src/mastra/agents/ai-w0rm-agent.ts`

---

**Remember: Ethical hacking requires authorization. Always follow the law.**
