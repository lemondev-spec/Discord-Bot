import discord
from discord.ext import commands
from discord import app_commands
import logging

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="show_balance", description="あなたの所持金を表示します")
    async def show_balance(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)
            balance = self.bot.user_balances.get(user_id, 0)
            await interaction.response.send_message(f'あなたの所持金は {balance} 任意の通貨名です。')
        except Exception as e:
            logging.error(f"Error in show_balance command: {e}")

    @app_commands.command(name="transfer_money", description="指定したユーザーに任意の通貨名を送金します")
    @app_commands.describe(member="送金先のユーザー", amount="送金する金額")
    async def transfer_money(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        try:
            giver_id = str(interaction.user.id)
            receiver_id = str(member.id)

            if giver_id not in self.bot.user_balances or self.bot.user_balances[giver_id] < amount:
                await interaction.response.send_message('所持金が足りません。', ephemeral=True)
                return

            if receiver_id not in self.bot.user_balances:
                self.bot.user_balances[receiver_id] = 0

            self.bot.user_balances[giver_id] -= amount
            self.bot.user_balances[receiver_id] += amount
            save_json(USER_BALANCES_FILE, self.bot.user_balances)

            await interaction.response.send_message(f'{member.mention} に {amount} 任意の通貨名を送金しました。')
        except Exception as e:
            logging.error(f"Error in transfer_money command: {e}")

    @app_commands.command(name="buy_role", description="指定したロールを購入します")
    @app_commands.describe(role_name="購入するロール名")
    async def buy_role(self, interaction: discord.Interaction, role_name: str):
        try:
            user_id = str(interaction.user.id)
            # メンション形式の場合はロールIDを抽出
            if role_name.startswith("<@&") and role_name.endswith(">"):
                role_id = role_name[3:-1]
                role = discord.utils.get(interaction.guild.roles, id=int(role_id))
            else:
                role = discord.utils.get(interaction.guild.roles, name=role_name)

            if role is None:
                await interaction.response.send_message('指定されたロールが見つかりません。', ephemeral=True)
                logging.error(f"Role not found: {role_name}")
                return

            role_id = str(role.id)
            if role_id not in self.bot.role_prices:
                await interaction.response.send_message('指定されたロールが見つかりません。', ephemeral=True)
                logging.error(f"Role ID not found in role_prices: {role_id}")
                return

            amount = self.bot.role_prices[role_id]['price']
            if self.bot.user_balances.get(user_id, 0) < amount:
                await interaction.response.send_message('所持金が足りません。', ephemeral=True)
                return

            member = interaction.guild.get_member(interaction.user.id)
            if role in member.roles:
                await interaction.response.send_message(f'すでに{role.name}ロールを持っています。', ephemeral=True)
                return

            self.bot.user_balances[user_id] -= amount
            await member.add_roles(role)
            save_json(USER_BALANCES_FILE, self.bot.user_balances)

            embed = discord.Embed(title='ロール購入完了', description=f'{role.name}ロールを購入しました！', color=0x00FF00)
            embed.set_thumbnail(url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logging.error(f"Error in buy_role command: {e}")

    @app_commands.command(name="list_roles", description="購入可能なロールとその価格を表示します")
    async def list_roles(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title='購入可能なロール', color=0x1E90FF)
            for role_id, data in self.bot.role_prices.items():
                role_name = data['name']
                price = data['price']
                embed.add_field(name=role_name, value=f'{price} 任意の通貨名', inline=True)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logging.error(f"Error in list_roles command: {e}")

    @app_commands.command(name="set_role_price", description="ロールの価格を設定します (管理者のみ)")
    @app_commands.describe(role_name="価格を設定するロール名", price="ロールの価格")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_role_price(self, interaction: discord.Interaction, role_name: str, price: int):
        try:
            # メンション形式の場合はロールIDを抽出
            if role_name.startswith("<@&") and role_name.endswith(">"):
                role_id = role_name[3:-1]
                role = discord.utils.get(interaction.guild.roles, id=int(role_id))
            else:
                role = discord.utils.get(interaction.guild.roles, name=role_name)

            if role is None:
                await interaction.response.send_message('指定されたロールが見つかりません。', ephemeral=True)
                logging.error(f"Role not found: {role_name}")
                return

            self.bot.role_prices[str(role.id)] = {"name": role.name, "price": price}
            save_json(ROLE_PRICES_FILE, self.bot.role_prices)
            await interaction.response.send_message(f'{role.name}ロールの価格を{price} 任意の通貨名に設定しました。')
        except Exception as e:
            logging.error(f"Error in set_role_price command: {e}")

    @app_commands.command(name="help_command", description="利用可能なコマンドのリストを表示します")
    async def help_command(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title='ヘルプ', description='利用可能なコマンドのリストです', color=0xFFA500)
            embed.add_field(name='/show_balance', value='あなたの所持金を表示します', inline=True)
            embed.add_field(name='/transfer_money @ユーザー 金額', value='指定したユーザーに任意の通貨名を送金します', inline=True)
            embed.add_field(name='/buy_role ロール名', value='指定したロールを購入します', inline=True)
            embed.add_field(name='/list_roles', value='購入可能なロールとその価格を表示します', inline=True)
            embed.add_field(name='/set_role_price ロール名 金額', value='ロールの価格を設定します (管理者のみ)', inline=True)
            embed.set_footer(text='おしゃれに装飾されたコマンドリストです')
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logging.error(f"Error in help_command command: {e}")

async def setup(bot):
    await bot.add_cog(Commands(bot))
