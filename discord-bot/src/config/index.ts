// src/config/index.ts
import dotenv from 'dotenv';

dotenv.config();

const config = {
    discordToken: process.env.DISCORD_TOKEN,
    prefix: process.env.PREFIX || '!',
};

export default config;