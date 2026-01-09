from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Hunter x Nen RPG System API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class ResourceValue(BaseModel):
    current: int = 10
    max: int = 10

class Resistances(BaseModel):
    cortante: int = 0
    perfurante: int = 0
    impacto: int = 0
    elemental: int = 0

class CharacterResources(BaseModel):
    pv: ResourceValue = Field(default_factory=ResourceValue)
    pa: ResourceValue = Field(default_factory=ResourceValue)
    defense: int = 10
    resistances: Resistances = Field(default_factory=Resistances)

class Attributes(BaseModel):
    FOR: int = 1
    VIG: int = 1
    DEX: int = 1
    INT: int = 1
    CAR: int = 1

class FactionReputation(BaseModel):
    value: int = 0
    notes: str = ""

class BasicTechniques(BaseModel):
    ten: str = "Amador"
    ren: str = "Amador"
    zetsu: str = "Amador"

class AdvancedTechniques(BaseModel):
    gyo_perception: bool = Field(default=False, alias="Gyô - Percepção")
    gyo_attack: bool = Field(default=False, alias="Gyô - Ataque")
    gyo_defense: bool = Field(default=False, alias="Gyô - Defesa")
    in_tech: bool = Field(default=False, alias="In")
    en: bool = Field(default=False, alias="En")
    shu: bool = Field(default=False, alias="Shu")
    ken: bool = Field(default=False, alias="Ken")
    
    model_config = ConfigDict(populate_by_name=True)

class Hatsu(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = ""
    category: str = "Base"
    range: str = ""
    cost: int = 0
    duration: str = ""
    target: str = ""
    execution: str = ""
    description: str = ""

class NenSystem(BaseModel):
    hatsuType: str = ""
    basicTechniques: BasicTechniques = Field(default_factory=BasicTechniques)
    advancedTechniques: Dict[str, bool] = Field(default_factory=lambda: {
        "Gyô - Percepção": False,
        "Gyô - Ataque": False,
        "Gyô - Defesa": False,
        "In": False,
        "En": False,
        "Shu": False,
        "Ken": False,
    })
    hatsus: List[Hatsu] = Field(default_factory=list)

class Weapon(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    damageType: str = "Cortante"
    damage: str = "1d6"
    critical: str = "20/x2"

class InventoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    details: str = ""
    weight: float = 0

class Lore(BaseModel):
    originAbility: str = ""
    history: str = ""
    personality: str = ""
    appearance: str = ""
    objectives: str = ""
    notes: str = ""

class BeastAbility(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    cost: int = 0
    description: str = ""

class BeastActions(BaseModel):
    attack: str = "1d6"
    heal: str = "1d4"

class BeastResources(BaseModel):
    pv: ResourceValue = Field(default_factory=ResourceValue)
    pe: Optional[ResourceValue] = None  # Only for wild beasts
    resistances: Resistances = Field(default_factory=Resistances)

class Beast(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "wild"  # "wild" or "nen"
    name: str = ""
    attributes: Attributes = Field(default_factory=Attributes)
    resources: BeastResources = Field(default_factory=BeastResources)
    skills: Dict[str, int] = Field(default_factory=dict)
    actions: BeastActions = Field(default_factory=BeastActions)
    abilities: List[BeastAbility] = Field(default_factory=list)

class Character(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    userId: Optional[str] = None
    
    # Identification
    name: str = ""
    level: int = 1
    origin: str = ""
    classes: List[str] = Field(default_factory=list)
    customClass: str = ""
    
    # Stats
    attributes: Attributes = Field(default_factory=Attributes)
    resources: CharacterResources = Field(default_factory=CharacterResources)
    skills: Dict[str, int] = Field(default_factory=dict)
    
    # Factions
    factions: Dict[str, FactionReputation] = Field(default_factory=dict)
    
    # Nen
    nen: NenSystem = Field(default_factory=NenSystem)
    
    # Equipment
    weapons: List[Weapon] = Field(default_factory=list)
    inventory: List[InventoryItem] = Field(default_factory=list)
    
    # Lore
    lore: Lore = Field(default_factory=Lore)
    classAbility: str = ""
    
    # Beasts
    beasts: List[Beast] = Field(default_factory=list)

class CharacterCreate(BaseModel):
    name: str
    userId: Optional[str] = None

class CharacterUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")

class RollRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    characterId: str
    characterName: str
    rolls: List[int]
    highest: int
    attributeValue: int
    skillBonus: int
    skillName: str
    attributeName: str
    penaltyApplied: bool = False
    penaltyValue: int = 0
    baseResult: int
    finalResult: int
    isCritical: bool = False
    isCriticalFail: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RollCreate(BaseModel):
    characterId: str
    characterName: str
    rolls: List[int]
    highest: int
    attributeValue: int
    skillBonus: int
    skillName: str
    attributeName: str
    penaltyApplied: bool = False
    penaltyValue: int = 0
    baseResult: int
    finalResult: int
    isCritical: bool = False
    isCriticalFail: bool = False

# Threat model for campaigns
class ThreatCombat(BaseModel):
    damage: str = "2d8+5"

class Threat(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campaignId: str
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    name: str = ""
    resources: CharacterResources = Field(default_factory=CharacterResources)
    attributes: Attributes = Field(default_factory=Attributes)
    skills: Dict[str, int] = Field(default_factory=lambda: {
        "Duelo": 0,
        "Vontade": 0,
        "Reflexos": 0,
        "Robustez": 0,
        "Caça": 0,
        "Controle de Nen": 0,
    })
    dueloAttribute: str = "FOR"
    nen: NenSystem = Field(default_factory=NenSystem)
    combat: ThreatCombat = Field(default_factory=ThreatCombat)
    generalAbilities: str = ""

class ThreatCreate(BaseModel):
    campaignId: str
    name: str

# ==================== ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Hunter x Nen RPG System API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Character CRUD
@api_router.post("/characters", response_model=Character)
async def create_character(input_data: CharacterCreate):
    character = Character(name=input_data.name, userId=input_data.userId)
    
    # Initialize default skills
    default_skills = {
        'Atletismo': 0, 'Duelo': 0, 'Robustez': 0, 'Resistência': 0,
        'Furtividade': 0, 'Acrobacia': 0, 'Reflexos': 0, 'Pontaria': 0, 'Roubo': 0,
        'Caça': 0, 'Investigação': 0, 'Medicina': 0, 'Profissão': 0, 'Astúcia': 0,
        'Persuasão': 0, 'Intimidação': 0, 'Vontade': 0, 'Intuição': 0, 'Tenacidade': 0,
        'Controle de Nen': 0,
    }
    character.skills = default_skills
    
    # Initialize default factions
    default_factions = {
        'hunter_association': FactionReputation(),
        'phantom_troupe': FactionReputation(),
        'zoldyck_family': FactionReputation(),
        'mafia': FactionReputation(),
        'world_government': FactionReputation(),
        'chimera_ants': FactionReputation(),
        'kurta_clan': FactionReputation(),
        'ninja_clans': FactionReputation(),
        'nen_community': FactionReputation(),
        'specific_kingdoms': FactionReputation(),
    }
    character.factions = {k: v.model_dump() for k, v in default_factions.items()}
    
    doc = character.model_dump()
    await db.characters.insert_one(doc)
    
    return character

@api_router.get("/characters", response_model=List[Character])
async def get_characters(userId: Optional[str] = None, skip: int = 0, limit: int = 50):
    query = {}
    if userId:
        query["userId"] = userId
    
    # Limit max results to prevent memory issues
    actual_limit = min(limit, 100)
    characters = await db.characters.find(query, {"_id": 0}).skip(skip).limit(actual_limit).to_list(actual_limit)
    return characters

@api_router.get("/characters/{character_id}", response_model=Character)
async def get_character(character_id: str):
    character = await db.characters.find_one({"id": character_id}, {"_id": 0})
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@api_router.put("/characters/{character_id}", response_model=Character)
async def update_character(character_id: str, update_data: dict):
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.characters.update_one(
        {"id": character_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Character not found")
    
    character = await db.characters.find_one({"id": character_id}, {"_id": 0})
    return character

@api_router.delete("/characters/{character_id}")
async def delete_character(character_id: str):
    result = await db.characters.delete_one({"id": character_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"message": "Character deleted successfully"}

# Roll history
@api_router.post("/rolls", response_model=RollRecord)
async def create_roll(input_data: RollCreate):
    roll = RollRecord(**input_data.model_dump())
    doc = roll.model_dump()
    await db.rolls.insert_one(doc)
    return roll

@api_router.get("/rolls", response_model=List[RollRecord])
async def get_rolls(characterId: Optional[str] = None, limit: int = 50):
    query = {}
    if characterId:
        query["characterId"] = characterId
    
    rolls = await db.rolls.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return rolls

@api_router.delete("/rolls")
async def clear_rolls(characterId: Optional[str] = None):
    query = {}
    if characterId:
        query["characterId"] = characterId
    
    await db.rolls.delete_many(query)
    return {"message": "Roll history cleared"}

# Threats CRUD
@api_router.post("/threats", response_model=Threat)
async def create_threat(input_data: ThreatCreate):
    threat = Threat(campaignId=input_data.campaignId, name=input_data.name)
    doc = threat.model_dump()
    await db.threats.insert_one(doc)
    return threat

@api_router.get("/threats", response_model=List[Threat])
async def get_threats(campaignId: str, skip: int = 0, limit: int = 50):
    actual_limit = min(limit, 100)
    threats = await db.threats.find({"campaignId": campaignId}, {"_id": 0}).skip(skip).limit(actual_limit).to_list(actual_limit)
    return threats

@api_router.get("/threats/{threat_id}", response_model=Threat)
async def get_threat(threat_id: str):
    threat = await db.threats.find_one({"id": threat_id}, {"_id": 0})
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    return threat

@api_router.put("/threats/{threat_id}", response_model=Threat)
async def update_threat(threat_id: str, update_data: dict):
    result = await db.threats.update_one(
        {"id": threat_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    threat = await db.threats.find_one({"id": threat_id}, {"_id": 0})
    return threat

@api_router.delete("/threats/{threat_id}")
async def delete_threat(threat_id: str):
    result = await db.threats.delete_one({"id": threat_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Threat not found")
    return {"message": "Threat deleted successfully"}

# Import threat from another campaign
@api_router.post("/threats/import/{threat_id}")
async def import_threat(threat_id: str, target_campaign_id: str):
    threat = await db.threats.find_one({"id": threat_id}, {"_id": 0})
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    # Create new threat with new ID
    new_threat = Threat(**threat)
    new_threat.id = str(uuid.uuid4())
    new_threat.campaignId = target_campaign_id
    new_threat.createdAt = datetime.now(timezone.utc).isoformat()
    
    doc = new_threat.model_dump()
    await db.threats.insert_one(doc)
    return new_threat

# ==================== CAMPAIGN MODELS ====================

class CampaignPlayer(BaseModel):
    odiserId: str
    odiserName: str
    odiserEmail: str
    characterId: str
    characterName: str = ""
    joinedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Campaign(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    masterId: str
    masterName: str = ""
    masterEmail: str = ""
    inviteCode: str = Field(default_factory=lambda: ''.join([chr(65 + (i * 7 + int(str(uuid.uuid4().int)[:2])) % 26) for i in range(6)]))
    players: List[CampaignPlayer] = Field(default_factory=list)
    playerIds: List[str] = Field(default_factory=list)
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CampaignCreate(BaseModel):
    name: str
    description: str = ""
    masterId: str
    masterName: str = ""
    masterEmail: str = ""

class CampaignCharacter(BaseModel):
    """Character copy stored within a campaign - modifications only affect this copy"""
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campaignId: str
    originalCharacterId: str
    odiserId: str
    data: Dict[str, Any] = Field(default_factory=dict)
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class JoinCampaignRequest(BaseModel):
    inviteCode: str
    odiserId: str
    odiserName: str
    odiserEmail: str
    characterId: str

class CampaignRoll(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campaignId: str
    odiserId: str
    odiserName: str
    characterName: str
    rollData: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ==================== CAMPAIGN ROUTES ====================

def generate_invite_code():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@api_router.post("/campaigns")
async def create_campaign(input_data: CampaignCreate):
    campaign = Campaign(
        name=input_data.name,
        description=input_data.description,
        masterId=input_data.masterId,
        masterName=input_data.masterName,
        masterEmail=input_data.masterEmail,
        inviteCode=generate_invite_code()
    )
    doc = campaign.model_dump()
    await db.campaigns.insert_one(doc)
    return campaign

@api_router.get("/campaigns")
async def get_user_campaigns(userId: str, skip: int = 0, limit: int = 50):
    actual_limit = min(limit, 100)
    
    # Get campaigns where user is master
    master_campaigns = await db.campaigns.find(
        {"masterId": userId}, 
        {"_id": 0, "id": 1, "name": 1, "description": 1, "inviteCode": 1, "players": 1, "playerIds": 1, "masterId": 1, "masterName": 1}
    ).skip(skip).limit(actual_limit).to_list(actual_limit)
    for c in master_campaigns:
        c["role"] = "master"
    
    # Get campaigns where user is player
    player_campaigns = await db.campaigns.find(
        {"playerIds": userId}, 
        {"_id": 0, "id": 1, "name": 1, "description": 1, "inviteCode": 1, "players": 1, "playerIds": 1, "masterId": 1, "masterName": 1}
    ).skip(skip).limit(actual_limit).to_list(actual_limit)
    for c in player_campaigns:
        c["role"] = "player"
    
    # Combine and return
    all_campaigns = master_campaigns + player_campaigns
    return all_campaigns

@api_router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@api_router.put("/campaigns/{campaign_id}")
async def update_campaign(campaign_id: str, update_data: dict):
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.campaigns.update_one(
        {"id": campaign_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    return campaign

@api_router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str, masterId: str):
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign["masterId"] != masterId:
        raise HTTPException(status_code=403, detail="Only the master can delete the campaign")
    
    await db.campaigns.delete_one({"id": campaign_id})
    await db.campaign_characters.delete_many({"campaignId": campaign_id})
    await db.threats.delete_many({"campaignId": campaign_id})
    await db.campaign_rolls.delete_many({"campaignId": campaign_id})
    
    return {"message": "Campaign deleted successfully"}

@api_router.post("/campaigns/join")
async def join_campaign(input_data: JoinCampaignRequest):
    # Find campaign by invite code
    campaign = await db.campaigns.find_one({"inviteCode": input_data.inviteCode}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    if campaign["masterId"] == input_data.odiserId:
        raise HTTPException(status_code=400, detail="You are the master of this campaign")
    
    if input_data.odiserId in campaign.get("playerIds", []):
        raise HTTPException(status_code=400, detail="You are already in this campaign")
    
    # Get the original character to copy
    original_char = await db.characters.find_one({"id": input_data.characterId}, {"_id": 0})
    if not original_char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Create campaign-specific copy of the character
    campaign_char = CampaignCharacter(
        campaignId=campaign["id"],
        originalCharacterId=input_data.characterId,
        odiserId=input_data.odiserId,
        data=original_char
    )
    await db.campaign_characters.insert_one(campaign_char.model_dump())
    
    # Add player to campaign
    new_player = CampaignPlayer(
        odiserId=input_data.odiserId,
        odiserName=input_data.odiserName,
        odiserEmail=input_data.odiserEmail,
        characterId=campaign_char.id,
        characterName=original_char.get("name", "")
    )
    
    await db.campaigns.update_one(
        {"id": campaign["id"]},
        {
            "$push": {
                "playerIds": input_data.odiserId,
                "players": new_player.model_dump()
            },
            "$set": {"updatedAt": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"success": True, "campaignId": campaign["id"], "characterId": campaign_char.id}

@api_router.post("/campaigns/{campaign_id}/leave")
async def leave_campaign(campaign_id: str, userId: str):
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if userId == campaign["masterId"]:
        raise HTTPException(status_code=400, detail="Master cannot leave the campaign")
    
    # Remove player from campaign
    await db.campaigns.update_one(
        {"id": campaign_id},
        {
            "$pull": {
                "playerIds": userId,
                "players": {"odiserId": userId}
            },
            "$set": {"updatedAt": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    # Remove campaign character
    await db.campaign_characters.delete_many({"campaignId": campaign_id, "odiserId": userId})
    
    return {"message": "Left campaign successfully"}

# Campaign Characters
@api_router.get("/campaigns/{campaign_id}/character/{user_id}")
async def get_campaign_character(campaign_id: str, user_id: str):
    char = await db.campaign_characters.find_one(
        {"campaignId": campaign_id, "odiserId": user_id},
        {"_id": 0}
    )
    if not char:
        raise HTTPException(status_code=404, detail="Campaign character not found")
    return char

@api_router.put("/campaigns/{campaign_id}/character/{character_id}")
async def update_campaign_character(campaign_id: str, character_id: str, update_data: dict):
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.campaign_characters.update_one(
        {"id": character_id, "campaignId": campaign_id},
        {"$set": {"data": update_data, "updatedAt": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign character not found")
    
    char = await db.campaign_characters.find_one({"id": character_id}, {"_id": 0})
    return char

# Campaign Rolls - for master to see
@api_router.post("/campaigns/{campaign_id}/rolls")
async def create_campaign_roll(campaign_id: str, roll_data: dict):
    roll = CampaignRoll(
        campaignId=campaign_id,
        odiserId=roll_data.get("odiserId", ""),
        odiserName=roll_data.get("odiserName", ""),
        characterName=roll_data.get("characterName", ""),
        rollData=roll_data.get("rollData", {})
    )
    await db.campaign_rolls.insert_one(roll.model_dump())
    return roll

@api_router.get("/campaigns/{campaign_id}/rolls")
async def get_campaign_rolls(campaign_id: str, limit: int = 50):
    rolls = await db.campaign_rolls.find(
        {"campaignId": campaign_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(limit)
    return rolls

# Get all player stats for master view
@api_router.get("/campaigns/{campaign_id}/player-stats")
async def get_player_stats(campaign_id: str):
    # Only fetch needed fields for stats
    chars = await db.campaign_characters.find(
        {"campaignId": campaign_id},
        {"_id": 0, "odiserId": 1, "id": 1, "data.name": 1, "data.resources.pv": 1, "data.resources.pa": 1, "updatedAt": 1}
    ).to_list(100)
    
    stats = []
    for char in chars:
        data = char.get("data", {})
        stats.append({
            "odiserId": char.get("odiserId"),
            "characterId": char.get("id"),
            "characterName": data.get("name", "Unknown"),
            "pv": data.get("resources", {}).get("pv", {"current": 0, "max": 0}),
            "pa": data.get("resources", {}).get("pa", {"current": 0, "max": 0}),
            "updatedAt": char.get("updatedAt")
        })
    
    return stats

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
import uvicorn
import os

if __name__ == "__main__":
    # O Render define a porta automaticamente na variável PORT
    port = int(os.environ.get("PORT", 10000))
    # É obrigatório usar host="0.0.0.0" para o servidor ficar online
    uvicorn.run(app, host="0.0.0.0", port=port)