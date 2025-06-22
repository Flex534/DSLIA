import discord
from discord.ext import commands

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role_name = "Alumno"
        role = discord.utils.get(member.guild.roles, name=role_name)
        if role:
            try:
                await member.add_roles(role)
                print(f"Se asignó el rol '{role_name}' a {member.name}")
                # Enviar mensaje de bienvenida al canal general
                canal_bienvenida = discord.utils.get(member.guild.text_channels, name="general")
                if canal_bienvenida:
                    await canal_bienvenida.send(f"¡Bienvenido/a {member.mention} al servidor! Ya tienes el rol de Alumno.")
            except discord.Forbidden:
                print(f"No tengo permisos para asignar el rol '{role_name}' a {member.name}")
            except Exception as e:
                print(f"Error al asignar el rol '{role_name}' a {member.name}: {e}")
        else:
            print(f"Rol '{role_name}' no encontrado en el servidor.")

    @commands.command()
    @commands.has_role("Docente")
    async def promover(self, ctx, miembro: discord.Member):
        rol_docente = discord.utils.get(ctx.guild.roles, name="Docente")
        if not rol_docente:
            await ctx.send("⚠️ El rol 'Docente' no existe en este servidor.")
            return
        try:
            await miembro.add_roles(rol_docente)
            await ctx.send(f"✅ {miembro.mention} ahora es Docente.")
        except discord.Forbidden:
            await ctx.send("❌ No tengo permisos para asignar el rol 'Docente'.")
        except Exception as e:
            await ctx.send(f"⚠️ Ocurrió un error: {e}")

    @commands.command()
    @commands.has_role("Docente")
    async def canal_privado(self, ctx):
        await ctx.send("Este comando solo lo pueden usar docentes.")

async def setup(bot):
    await bot.add_cog(Roles(bot))