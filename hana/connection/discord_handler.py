import asyncio
from concurrent.futures import ThreadPoolExecutor
from langchain_core.messages import HumanMessage
from discord.ext import commands

class Discord:
    def __init__(self,
                 bot,
                 hana,
                 executor,
                 token,
                 ):
        
        self.bot = bot
        self.hana = hana
        self.executor = executor
        self.token = token
        
        self._events()
        self._commands()

    def _events(self):
        @self.bot.event
        async def on_ready():
            print(f'Bot logged in as {self.bot.user}')
        
        @self.bot.event
        async def on_message(message):
            await self.bot.process_commands(message)
            
            if message.author == self.bot.user:
                return

            if message.content.startswith("Hana"):
                conversant_name = message.author.name
                if conversant_name == "futurio16":
                    conversant_name = "Futurio"
                else: #block other
                    return
                
                input_state = {"messages": [HumanMessage(message.content)], "conversant": conversant_name, "hana_response": "", "channel": "text"}

                loop = asyncio.get_event_loop()
                response_text = await loop.run_in_executor(self.executor, self.hana.AskHana, input_state)
                
                await message.channel.send(response_text)
    
    def _commands(self):
        @self.bot.command(name='join')
        async def join(ctx):
            if ctx.author.voice is None or ctx.author.voice.channel is None:
                await ctx.send("You need to join a voice channel first.")
                return

            voice_channel = ctx.author.voice.channel

            if ctx.voice_client is not None:
                if ctx.voice_client.channel.id == voice_channel.id:
                    await ctx.send("Hana is already in this voice channel.")
                    return
                await ctx.voice_client.move_to(voice_channel)
                await ctx.send(f"Switched to: {voice_channel.name}")
            else:
                await voice_channel.connect()
                await ctx.send(f"Joined voice channel: {voice_channel.name}")

        @self.bot.command(name='leave')
        async def leave(ctx):
            if ctx.voice_client is not None:
                await ctx.voice_client.disconnect()
                await ctx.send("Left voice channel.")
            else:
                await ctx.send("Hana is not in any voice channel.")

    def run(self):
        try:
            self.bot.run(self.token)
        except KeyboardInterrupt:
            print("\n\n=== Hana Discord Bot is stopped ===")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        print("Cleaning up Discord bot resources...")
        if self.executor:
            self.executor.shutdown(wait=True)