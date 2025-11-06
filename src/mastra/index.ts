import { Mastra } from '@mastra/core/mastra';
import { PinoLogger } from '@mastra/loggers';
import { weatherWorkflow, securityScanWorkflow } from './workflows';
import { weatherAgent, aiW0rmAgent, aiW0rmCyborgG7 } from './agents';

export const mastra = new Mastra({
  workflows: { 
    weatherWorkflow,
    securityScanWorkflow,
  },
  agents: { 
    weatherAgent,
    aiW0rmAgent,
    aiW0rmCyborgG7,
  },
  logger: new PinoLogger({
    name: 'Mastra',
    level: 'info',
  }),
  observability: {
    default: {
      enabled: true,
    },
  },
});
