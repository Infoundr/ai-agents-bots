import { ChatOpenAI } from '@langchain/openai';
import { HumanMessage, AIMessage } from '@langchain/core/messages';
import { ChatPromptTemplate, MessagesPlaceholder } from '@langchain/core/prompts';
import { logger } from '../utils/logger';

interface BotConfig {
    name: string;
    role: string;
    expertise: string;
    personality: string;
    context?: string;
    examplePrompts?: string[];
}

export class Bot {
    private chatModel: ChatOpenAI;
    private messageHistory: (HumanMessage | AIMessage)[];
    private prompt: ChatPromptTemplate;
    private chain: any;

    constructor(config: BotConfig) {
        this.chatModel = new ChatOpenAI({
            modelName: "gpt-4",
            temperature: 0.7,
            apiKey: process.env.OPENAI_API_KEY,
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
        let message = `You are ${config.name}, ${config.role}. Your expertise is in ${config.expertise}. Personality: ${config.personality}`;

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
            logger.error(`Error getting response from ${this.constructor.name}:`, error);
            throw error;
        }
    }
}

// Define the expert bots
export const BOTS = {
    "Benny": new Bot({
        name: "Benny",
        role: "Financial Decision Making Expert from Payd",
        expertise: "fintech strategies, payment solutions, financial planning for startups",
        personality: "Professional, data-driven, focused on financial innovation",
        context: `
        Fundraising Experience:
        - For my first funding round, I structured a small pre-seed round from angel investors and grants targeted at my sector.
        - I focused on getting just enough capital to prove the concept before seeking larger institutional funding.
        - Key metrics that helped attract investors included customer traction, revenue growth rate, and market validation through partnerships.
        - An early mistake I made was underestimating our burn rate and raising less than needed, which forced seeking another round sooner than expected.
        - For valuation and equity splits, I used a SAFE agreement for flexibility and avoided giving up too much equity early on.
        - I brought in advisors to help with fundraising negotiations.
        
        FinTech Regulatory Navigation:
        - I worked with legal experts to ensure we met financial compliance requirements in different African markets before pitching to investors.
        - Being proactive about regulatory concerns reassured investors about potential risks in this space.`
    }),
    // Add more bots here...
}; 