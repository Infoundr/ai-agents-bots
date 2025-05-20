import { Client, GatewayIntentBits } from 'discord.js';
import { registerEventHandlers } from './events';
import { config } from 'dotenv';

config();

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ],
});

registerEventHandlers(client);

client.login(process.env.DISCORD_TOKEN);