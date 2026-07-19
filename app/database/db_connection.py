import urllib.parse
import motor.motor_asyncio
from app.core.config import access

username=access.mongodb_username
cluster_name=access.mongodb_clustername
password=urllib.parse.quote_plus(access.mongodb_password)

mongodb_url=f"mongodb+srv://{username}:{password}@{cluster_name}/?appName={username}"

client= motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
db=client["portfolio_product"]