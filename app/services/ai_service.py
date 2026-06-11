import os
from sqlalchemy import inspect
from app.db.database import engine
from google import genai
from dotenv import load_dotenv
import sqlglot
from sqlglot import exp

from app.repositories.analytics_repository import execute_query

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_ID = "gemini-2.5-flash"

ALLOWED_TABLES = {"products", "audiences", "campaigns", "performance_metrics"}

session_storage = {}

def get_session_history_string(session_id: str) -> str:
    if session_id not in session_storage:
        return "No prior conversation history.\n"
    
    context = "CONVERSATION HISTORY (Use this to resolve pronouns like 'those', 'them', 'the cheap ones'):\n"
    for turn in session_storage[session_id][-6:]: # Turn
        role_label = "User Question" if turn["role"] == "user" else "Assistant Response"
        context += f"- {role_label}: {turn['text']}\n"
    return context

def get_database_schema_context() -> str:
    inspector = inspect(engine)
    schema_context = "DATABASE SCHEMA METADATA:\n"
    
    target_tables = ["products", "campaigns", "audiences", "performance_metrics"]
    
    for table_name in inspector.get_table_names():
        if table_name not in target_tables:
            continue
            
        schema_context += f"Table Name: '{table_name}'\nColumns:\n"
        for column in inspector.get_columns(table_name):
            schema_context += f"  - {column['name']} (Type: {str(column['type'])})\n"
        schema_context += "\n"
        
    return schema_context

def detect_intent(user_message: str, history_context: str) -> str:
    prompt = f"""
    You are a classification routing engine for a business analytics platform.
    Analyze the user input given the conversation history context and classify it into exactly one token.

    {history_context}
    Current User Input: "{user_message}"
    
    Classification rules:
    - 'data_query': ANY request for business data including follow-ups, corrections, or clarifications about previous data results. If the conversation history contains a data query and the user is refining or correcting their question, classify as 'data_query'.
    - 'general': greetings or completely unrelated conversation with NO business context.
    - 'clarification': ONLY when there is absolutely no business context in both the message AND conversation history.

    IMPORTANT: When in doubt between 'data_query' and 'clarification', always choose 'data_query' if there is any business entity mentioned (product name, campaign, audience, metric).

    Output only the exact token name string ('data_query', 'general', or 'clarification') without markdown or punctuation.
    """
    response = client.models.generate_content(model=MODEL_ID, contents=prompt, config={"temperature": 0})
    return response.text.strip().lower()

def is_query_safe(sql_string: str) -> bool:
    try:
        statement = sqlglot.parse_one(sql_string.strip())
    except Exception:
        return False

    if not isinstance(statement, (exp.Select, exp.With)):
        return False

    for node in statement.walk():
        if isinstance(node, (exp.Drop, exp.Delete, exp.Update, exp.Insert,
                             exp.Alter, exp.TruncateTable)):
            return False
        
    cte_names = {cte.alias.lower() for cte in statement.find_all(exp.CTE)}

    # Cek whitelist tabel, skip CTE names
    tables = {t.name.lower() for t in statement.find_all(exp.Table)}
    real_tables = tables - cte_names  # ← hapus CTE names dari check

    if not real_tables.issubset(ALLOWED_TABLES):
        return False

    return True

def process_business_intelligence_chat(user_message: str, session_id: str = "session_default") -> dict:
    if session_id not in session_storage:
        session_storage[session_id] = []
        
    history_context = get_session_history_string(session_id)
    intent = detect_intent(user_message, history_context)
    
    session_storage[session_id].append({"role": "user", "text": user_message})
    
    if intent == "general":
        bot_reply = "Halo! Saya adalah asisten analitik data internal Anda. Anda dapat menanyakan info product, performa kampanye marketing, atau data audience saat ini."
        session_storage[session_id].append({"role": "assistant", "text": bot_reply})
        return {"intent": intent, "response": bot_reply, "generated_sql": None}
        
    elif intent == "clarification":
        bot_reply = "Maaf, pertanyaan tersebut kurang spesifik atau di luar konteks bisnis. Bisakah Anda memperjelas data product, campaign marketing, atau audience apa yang ingin dicari?"
        session_storage[session_id].append({"role": "assistant", "text": bot_reply})
        return {"intent": intent, "response": bot_reply, "generated_sql": None}
        
    elif intent == "data_query":
        try:
            db_schema = get_database_schema_context()
            
            sql_generation_prompt = f"""
            You are an expert data engineer translating natural language into valid PostgreSQL queries.
            
            {db_schema}
            
            {history_context}
            Current User Question: "{user_message}"

            CRITICAL RULES:
            1. Return ONLY the raw SQL statement executable code. Do NOT wrap in markdown blocks.
            2. The query must strictly be a read-only query (SELECT).
            3. CRITICAL: Always apply a sensible 'LIMIT 100' at the end of the query unless a smaller LIMIT is requested.
            4. For string/text filtering (e.g., categories, names, generations), ALWAYS use the 'ILIKE' operator instead of '=' (e.g., category ILIKE 'skincare') OR use LOWER() on both sides to avoid case-sensitivity issues.
            5. The user might type in lowercase, but the database values might be Capitalized (e.g., 'Skincare', 'Gen Z'). Using 'ILIKE' or 'LOWER()' guarantees a match.
            6. When querying clicks, conversions, or revenue, ALWAYS use SUM() and GROUP BY to aggregate metrics per product/campaign. Never return raw metric rows without aggregation.
            SQL Output:
            """
            
            sql_response = client.models.generate_content(model=MODEL_ID, contents=sql_generation_prompt, config={"temperature": 0})
            
            if not sql_response.text:
                bot_reply = "Akses Ditolak: Query tidak dapat diproses."
                return {"intent": "blocked", "response": bot_reply, "generated_sql": None}
            
            generated_sql = sql_response.text.strip().replace("```sql", "").replace("```", "").strip()
            
            if not is_query_safe(generated_sql):
                bot_reply = "Akses Ditolak: Deteksi query berbahaya. Sistem mengizinkan eksekusi read only."
                return {"intent": "blocked", "response": bot_reply, "generated_sql": generated_sql}
            
            raw_db_results = execute_query(generated_sql)
            
            summarization_prompt = f"""
            You are a helpful business intelligence assistant. Translate the structured database results into a professional, human-friendly response written in Indonesian.

            User Question: {user_message}
            Executed SQL: {generated_sql}
            Database Raw Output Result: {str(raw_db_results)}

            Rules for your response:
            - Formulate a clear summary in Indonesian.
            - Never mention technical database terms (SQL, columns, arrays) unless explicitly asked.
            - If empty, inform politely that the data matching the criteria was not found.
            - CRITICAL: Only state facts that exist in the Database Raw Output. Do NOT invent, assume, or fill in missing values.
            - When user asks follow-up about a specific item mentioned in conversation history, only return data for that specific item, not aggregated totals.
            """
            
            final_summary = client.models.generate_content(model=MODEL_ID, contents=summarization_prompt, config={"temperature": 0.3})
            bot_reply = final_summary.text.strip()
            
            session_storage[session_id].append({"role": "assistant", "text": bot_reply})
            
            return {
                "intent": intent,
                "response": bot_reply,
                "generated_sql": generated_sql
            }
            
        except Exception as err:
            return {
                "intent": "error",
                "response": f"Mohon maaf, terjadi gangguan teknis saat memproses ekstraksi analitik: {str(err)}",
                "generated_sql": locals().get('generated_sql', None)
            }
            
    return {"intent": "error", "response": "Sistem gagal mengenali intensitas pesan.", "generated_sql": None}