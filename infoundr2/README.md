# Create OpenChat Bot

A CLI tool for instantly creating OpenChat bots.

[![npm version](https://img.shields.io/npm/v/create-openchat-bot.svg)](https://www.npmjs.com/package/create-openchat-bot)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Registering Your Bot](#registering-your-bot)
- [SDK Documentation for Rust bots](#sdk-documentation-for-rust-bots)
- [Bot Types](#bot-types)
- [SDKs](#sdks)
- [Overview](#overview)
- [License](#license)

## Prerequisites

For both onchain and offchain bot, you need to have installed the following tools: 
- [Rust](https://www.rust-lang.org/tools/install)
- [DFX](https://internetcomputer.org/docs/current/developer-docs/setup/install/) (for identity management)

## Installation

```bash
npm install -g create-openchat-bot
```

## Usage

```bash
npx create-openchat-bot
```

This will:
1. Ask you which type of bot you want to create (offchain or onchain)
2. Ask for your bot's name
3. Create a new directory with the template
4. Set up the necessary configuration
5. Run the appropriate setup script

## Registering Your Bot

Follow the instructions [here](https://github.com/ICP-HUBS-DevRels-Syndicate/openchat-bots/blob/main/REGISTER-BOT.md) to register your bot with OC and test it out.

> **Note:** This package is in beta mode and currently only supports the Rust SDK. The Motoko and TypeScript SDKs are in the pipeline.

## SDK Documentation for Rust bots: 
You can now check out the SDK documentation for rust bots [here](https://github.com/open-chat-labs/open-chat-bots/tree/main/rs/sdk)

## Bot Types

### Offchain Bot
- Runs on your local machine
- Good for development and testing
- No Internet Computer deployment needed
- Quick setup and iteration

### Onchain Bot
- Deploys to the Internet Computer
- Runs on the blockchain
- More complex setup
- Requires DFX and Internet Computer tools

## SDKs

SDKs are available in different languages: 
- Rust SDK, see the documentation [here](https://github.com/open-chat-labs/open-chat-bots/blob/main/rs/README.md)
- Typescript SDK, see the documentation [here](https://github.com/open-chat-labs/open-chat-bots/blob/main/ts/README.md)
- Motoko SDK, see the documentation [here](https://github.com/open-chat-labs/open-chat-bots/blob/main/motoko/README.md)

## License

MIT License

Copyright (c) 2025 ICP-HUBS-DevRels-Syndicate

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE. 