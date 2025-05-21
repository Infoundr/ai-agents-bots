import { ChatOpenAI } from 'langchain/chat_models/openai';
import { HumanMessage, AIMessage, SystemMessage } from 'langchain/schema';
import { ChatPromptTemplate } from 'langchain/prompts';

export class Bot {
    private chatModel: ChatOpenAI;
    private messageHistory: Array<HumanMessage | AIMessage | SystemMessage> = [];
    private prompt: ChatPromptTemplate;

    constructor(
        public name: string,
        public role: string,
        public expertise: string,
        public personality: string,
        public context: string = "",
        public examplePrompts: string[] = []
    ) {
        this.chatModel = new ChatOpenAI({
            modelName: "gpt-4",
            temperature: 0.7,
            openAIApiKey: process.env.OPENAI_API_KEY,
        });

        const systemMessage = this.createSystemMessage();
        this.messageHistory.push(new SystemMessage(systemMessage));
    }

    private createSystemMessage(): string {
        let message = `You are ${this.name}, ${this.role}. Your expertise is in ${this.expertise}. Personality: ${this.personality}`;
        
        if (this.context) {
            message += `\n\nExperience and Knowledge:\n${this.context}`;
        }

        return message;
    }

    async getResponse(input: string): Promise<string> {
        try {
            this.messageHistory.push(new HumanMessage(input));
            
            const response = await this.chatModel.call(this.messageHistory);
            this.messageHistory.push(new AIMessage(response.content));
            
            return response.content;
        } catch (error) {
            console.error('Error getting response:', error);
            throw error;
        }
    }
}

// Export BOTS object with  bot instances
export const BOTS: Record<string, Bot> = {
    "Benny": new Bot(
        "Benny",
        "Financial Decision Making Expert",
        "fintech strategies, payment solutions",
        "Professional, data-driven",
        "Experience in fundraising and financial planning..."
    ),
   
};