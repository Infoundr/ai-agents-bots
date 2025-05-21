import { ChatOpenAI } from '@langchain/openai';
import { HumanMessage, AIMessage } from '@langchain/core/messages';
import { ChatPromptTemplate, MessagesPlaceholder } from '@langchain/core/prompts';
import { logger } from '../utils/logger';
import axios from 'axios';

interface BotConfig {
    name: string;
    role: string;
    expertise: string;
    personality?: string;
    context?: string;
    examplePrompts?: string[];
}

export class Bot {
    private chatModel: ChatOpenAI;
    private messageHistory: (HumanMessage | AIMessage)[];
    private prompt: ChatPromptTemplate;
    private chain: any;
    private config: BotConfig;
    public readonly role: string;
    public readonly expertise: string;

    constructor(config: BotConfig) {
        this.config = config;
        this.role = config.role;
        this.expertise = config.expertise;
        
        if (!process.env.OPENAI_API_KEY) {
            throw new Error('OPENAI_API_KEY is not set');
        }

        this.chatModel = new ChatOpenAI({
            modelName: "gpt-4",
            temperature: 0.7,
            openAIApiKey: process.env.OPENAI_API_KEY,
            timeout: 30000,
            maxRetries: 3
        });

        this.messageHistory = [];

        const systemMessage = this.buildSystemMessage(config);
        this.prompt = ChatPromptTemplate.fromMessages([
            ["system", systemMessage],
            new MessagesPlaceholder("history"),
            ["human", "{input}"]
        ]);

        this.chain = this.prompt.pipe(this.chatModel);
    }

    private buildSystemMessage(config: BotConfig): string {
        let message = `You are ${config.name}, ${config.role}. Your expertise is in ${config.expertise}.`;

        if (config.personality) {
            message += ` Personality: ${config.personality}`;
        }

        if (config.context) {
            message += `\n\nExperience and Knowledge:\n${config.context}`;
        }

        message += `\n\nWhen responding:
1. Always speak in first person as if you are actually ${config.name}, not an AI assistant
2. Refer to specific personal experiences mentioned in your background
3. Use casual, conversational language rather than formal explanations
4. Start responses with phrases like "From my experience..." or "When I built my company..."
5. Include specific challenges you faced and how you overcame them
6. Avoid comprehensive, exhaustive lists that sound AI-generated
7. Occasionally mention specific mistakes you made and what you learned
8. Use a more opinionated tone based on your personality
9. Be concise - successful entrepreneurs respect others' time`;

        return message;
    }

    async getResponse(input: string): Promise<string> {
        try {
            this.messageHistory.push(new HumanMessage(input));
            
            const response = await this.chain.invoke({
                history: this.messageHistory,
                input: input
            });

            this.messageHistory.push(new AIMessage(response.content));
            return response.content;
        } catch (error) {
            logger.error(`Error getting response from ${this.config.name}:`, error);
            throw error;
        }
    }
}

// Function to fetch bot info from API
async function fetchBotInfo(): Promise<Record<string, BotConfig>> {
    try {
        logger.info('Fetching bot info from API...');
        const response = await axios.get('http://154.38.174.112:5005/api/bot_info');
        logger.info('API Response received:', response.data);
        
        if (!response.data || Object.keys(response.data).length === 0) {
            throw new Error('No bot data received from API');
        }
        
        const botCount = Object.keys(response.data).length;
        logger.info(`Fetched ${botCount} bots from API: ${Object.keys(response.data).join(', ')}`);
        return response.data;
    } catch (error) {
        logger.error('Error fetching bot info:', error);
        if (axios.isAxiosError(error)) {
            logger.error('API Error details:', {
                status: error.response?.status,
                statusText: error.response?.statusText,
                data: error.response?.data
            });
        }
        throw error;
    }
}

// Initialize bots from API
export async function initializeBots(): Promise<Record<string, Bot>> {
    try {
        logger.info('Starting bot initialization...');
        const botConfigs = await fetchBotInfo();
        const bots: Record<string, Bot> = {};

        for (const [name, config] of Object.entries(botConfigs)) {
            try {
                logger.info(`Initializing bot ${name} with config:`, config);
                bots[name] = new Bot({
                    ...config,
                    personality: config.personality || "Professional, knowledgeable, and helpful"
                });
                logger.info(`Successfully initialized bot: ${name}`);
            } catch (error) {
                logger.error(`Error initializing bot ${name}:`, error);
                if (error instanceof Error) {
                    logger.error(`Error details for ${name}: ${error.message}`);
                }
            }
        }

        if (Object.keys(bots).length === 0) {
            throw new Error('No bots were successfully initialized');
        }

        const botNames = Object.keys(bots).join(', ');
        logger.info(`Successfully initialized ${Object.keys(bots).length} bots: ${botNames}`);
        return bots;
    } catch (error) {
        logger.error('Error initializing bots:', error);
        if (error instanceof Error) {
            logger.error(`Initialization error details: ${error.message}`);
        }
        throw error;
    }
}

// Export an empty BOTS object that will be populated after initialization
export let BOTS: Record<string, Bot> = {}; 