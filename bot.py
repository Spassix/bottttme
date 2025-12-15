import logging
import os
import json
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.error import Conflict

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token du bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID de l'admin
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Chemins des liens
MINI_APP_URL = os.getenv("MINI_APP_URL")
TELEGRAM_CHANNEL_URL = os.getenv("TELEGRAM_CHANNEL_URL")
SNAPCHAT_URL = os.getenv("SNAPCHAT_URL")
POTATO_URL = os.getenv("POTATO_URL")

# Chemin de l'image (à ajouter dans le dossier)
IMAGE_PATH = os.getenv("IMAGE_PATH", "mexicain_logo.png")

# Fichier pour stocker les utilisateurs
USERS_FILE = os.getenv("USERS_FILE", "users.json")

# Vérifier que les variables essentielles sont définies
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN n'est pas défini dans le fichier .env")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID n'est pas défini dans le fichier .env")


def load_users():
    """Charge la liste des utilisateurs depuis le fichier"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            return set()
    return set()


def save_user(user_id):
    """Sauvegarde un utilisateur dans le fichier"""
    users = load_users()
    users.add(user_id)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(users), f)


def is_content_safe(text: str) -> bool:
    """Vérifie si le contenu est conforme aux ToS de Telegram"""
    # Liste de mots-clés à éviter (contenu potentiellement problématique)
    prohibited_keywords = [
        'drogue', 'drug', 'cannabis', 'weed', 'coke', 'cocaïne',
        'héroïne', 'ecstasy', 'mdma', 'lsd', 'shroom', 'champignon',
        'dealer', 'vendeur', 'vente', 'acheter', 'commande'
    ]
    
    text_lower = text.lower()
    # Vérifier si le texte contient des mots-clés interdits
    for keyword in prohibited_keywords:
        if keyword in text_lower:
            return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère la commande /start"""
    user = update.effective_user
    
    # Sauvegarder l'utilisateur
    save_user(user.id)
    
    # Création du clavier avec les boutons
    keyboard = []
    if MINI_APP_URL:
        keyboard.append([InlineKeyboardButton("🛒 SHOP", web_app=WebAppInfo(url=MINI_APP_URL))])
    if SNAPCHAT_URL:
        keyboard.append([InlineKeyboardButton("📞 CONTACT", url=SNAPCHAT_URL)])
    if TELEGRAM_CHANNEL_URL:
        keyboard.append([InlineKeyboardButton("📨 TELEGRAM", url=TELEGRAM_CHANNEL_URL)])
    if POTATO_URL:
        keyboard.append([InlineKeyboardButton("🚀 POTATO", url=POTATO_URL)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Message de bienvenue (HTML pour éviter les problèmes de parsing)
    welcome_message = """<b>Bienvenue chez Mexicain59🥇</b>

Bienvenue sur notre plateforme ! Découvrez nos services et restez connecté avec notre communauté.

Utilisez les boutons ci-dessous pour accéder à nos différents canaux de communication et services.

<b>ℹ️ Information importante :</b>
Ce bot est conforme aux conditions d'utilisation de Telegram. Tous les contenus et services proposés respectent les lois en vigueur.

Appuyez sur /start pour actualiser le menu🔄"""
    
    # Envoi de l'image si elle existe, sinon juste le message
    try:
        if os.path.exists(IMAGE_PATH):
            with open(IMAGE_PATH, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=welcome_message,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
        else:
            await update.message.reply_text(
                welcome_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'image: {e}")
        # En cas d'erreur, envoyer sans formatage
        welcome_message_plain = """Bienvenue chez Mexicain59🥇

Bienvenue sur notre plateforme ! Découvrez nos services et restez connecté avec notre communauté.

Utilisez les boutons ci-dessous pour accéder à nos différents canaux de communication et services.

ℹ️ Information importante :
Ce bot est conforme aux conditions d'utilisation de Telegram. Tous les contenus et services proposés respectent les lois en vigueur.

Appuyez sur /start pour actualiser le menu🔄"""
        await update.message.reply_text(
            welcome_message_plain,
            reply_markup=reply_markup
        )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère la commande /broadcast pour les admins"""
    user = update.effective_user
    
    # Vérifier si l'utilisateur est admin
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Vous n'avez pas la permission d'utiliser cette commande.")
        return
    
    # Vérifier si un message a été fourni
    if not context.args:
        await update.message.reply_text(
            "<b>📢 Utilisation de /broadcast:</b>\n\n"
            "Envoyez votre message après la commande:\n"
            "<code>/broadcast Votre message ici</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Récupérer le message à diffuser
    message_text = " ".join(context.args)
    
    # Vérifier la sécurité du contenu
    if not is_content_safe(message_text):
        await update.message.reply_text(
            "❌ <b>Message rejeté</b>\n\n"
            "Le message contient du contenu qui pourrait violer les conditions d'utilisation de Telegram.\n"
            "Veuillez reformuler votre message de manière plus neutre et professionnelle.",
            parse_mode=ParseMode.HTML
        )
        logger.warning(f"Admin {user.id} a tenté d'envoyer un message potentiellement problématique")
        return
    
    # Charger tous les utilisateurs
    users = load_users()
    
    if not users:
        await update.message.reply_text(
            "⚠️ Aucun utilisateur trouvé dans la base de données.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Envoyer le message de confirmation
    await update.message.reply_text(
        f"<b>📢 Diffusion en cours...</b>\n\n"
        f"Message: {message_text}\n"
        f"Destinataires: {len(users)} utilisateur(s)",
        parse_mode=ParseMode.HTML
    )
    
    # Diffuser le message à tous les utilisateurs
    success_count = 0
    fail_count = 0
    
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode=None
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi à {user_id}: {e}")
            fail_count += 1
    
    # Envoyer le rapport final
    await update.message.reply_text(
        f"<b>✅ Diffusion terminée!</b>\n\n"
        f"✅ Envoyé avec succès: {success_count}\n"
        f"❌ Échecs: {fail_count}\n"
        f"📊 Total: {len(users)}",
        parse_mode=ParseMode.HTML
    )
    
    logger.info(f"Admin {user.id} a diffusé un message à {success_count} utilisateurs")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère la commande /help"""
    help_text = """<b>📖 Aide - Bot Mexicain59</b>

<b>Commandes disponibles :</b>
/start - Afficher le menu principal
/help - Afficher cette aide

<b>À propos :</b>
Ce bot vous permet d'accéder à nos différents canaux de communication et services.

<b>Conformité :</b>
Ce bot respecte les conditions d'utilisation de Telegram et les lois en vigueur.

Pour toute question, utilisez les boutons du menu principal."""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les clics sur les boutons inline"""
    query = update.callback_query
    await query.answer()


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les erreurs"""
    logger.error(f"Exception while handling an update: {context.error}")
    if isinstance(context.error, Conflict):
        logger.warning("Conflit détecté: une autre instance du bot est en cours d'exécution")
        # Attendre un peu avant de réessayer
        await asyncio.sleep(5)


def main() -> None:
    """Fonction principale pour démarrer le bot"""
    # Créer l'application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Ajouter les handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Ajouter le gestionnaire d'erreurs
    application.add_error_handler(error_handler)
    
    # Définir les commandes du bot
    commands = [
        BotCommand("start", "Démarrer le bot et voir le menu"),
        BotCommand("broadcast", "Diffuser un message (Admin uniquement)"),
        BotCommand("help", "Afficher l'aide et les informations")
    ]
    
    async def post_init(application: Application) -> None:
        await application.bot.set_my_commands(commands)
    
    application.post_init = post_init
    
    # Vérifier si on est sur Render (utiliser webhook) ou en local (utiliser polling)
    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
    render_port = os.getenv("PORT", "8000")
    
    if render_external_url:
        # Mode webhook pour Render
        webhook_path = "/webhook"
        webhook_url = f"{render_external_url}{webhook_path}"
        logger.info(f"Mode webhook activé: {webhook_url}")
        
        async def webhook_post_init(app: Application) -> None:
            await post_init(app)
            await app.bot.set_webhook(url=webhook_url)
            logger.info("Webhook configuré avec succès")
        
        application.post_init = webhook_post_init
        
        # Démarrer le serveur webhook
        application.run_webhook(
            listen="0.0.0.0",
            port=int(render_port),
            url_path=webhook_path,
            webhook_url=webhook_url,
            allowed_updates=Update.ALL_TYPES
        )
    else:
        # Mode polling pour le développement local
        logger.info("Mode polling activé (développement local)")
        try:
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True  # Ignorer les mises à jour en attente
            )
        except Conflict as e:
            logger.error(f"Conflit: {e}")
            logger.info("Arrêtez l'autre instance du bot avant de relancer")


if __name__ == '__main__':
    main()

