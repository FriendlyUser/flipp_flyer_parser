import os
import datetime
import psycopg2
# Removed openai import
from dotenv import load_dotenv
# Removed Langchain imports
# from langchain.prompts import PromptTemplate
# from langchain_google_genai import GoogleGenerativeAI

# Added agno imports
from agno.agent import Agent
from agno.models.google import Gemini

load_dotenv()

# Removed init_llm function as Agent initialization is straightforward

def main():
    # 1. Load environment variables
    # load_dotenv() # Already called globally

    # Retrieve database URL and GOOGLE_API_KEY from environment
    connection_url = os.getenv("DATABASE_URL")
    google_api_key = os.getenv("GOOGLE_API_KEY") # Ensure GOOGLE_API_KEY is set

    if not google_api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        return
    if not connection_url:
        print("Error: DATABASE_URL environment variable not set.")
        return

    conn = None # Initialize conn to None for finally block
    cursor = None # Initialize cursor to None for finally block

    # 2. Connect to PostgreSQL
    try:
        conn = psycopg2.connect(connection_url)
        cursor = conn.cursor()

        # 3. Query rows for date range [today, next Friday]
        today = datetime.date.today()
        # Next Friday calculation
        # Monday=0, Tuesday=1, ... Sunday=6, so Friday=4
        days_until_friday = (4 - today.weekday() + 7) % 7 # Ensure positive days
        next_friday = today + datetime.timedelta(days=days_until_friday)

        # If today is Friday, next_friday should be today
        if days_until_friday == 0:
            next_friday = today

        print(f"Querying items on sale between {today} and {next_friday}")

        query = """
            SELECT
                label,               -- 0
                flyer_path,          -- 1
                product_name,        -- 2
                data_product_id,     -- 3
                savings,             -- 4
                current_price,       -- 5
                start_date,          -- 6
                end_date,            -- 7
                description,         -- 8
                size,                -- 9
                quantity,            -- 10
                product_type,        -- 11
                frozen,              -- 12
                see_more_link,       -- 13
                store                -- 14
            FROM grocery
            -- Items whose sale period overlaps [today, next_friday]
            WHERE start_date <= %s
              AND end_date >= %s
              AND store != 'saveon' -- Excluding 'saveon' as per original code
        """
        cursor.execute(query, (next_friday, today))
        rows = cursor.fetchall()
        print(f"Found {len(rows)} potentially matching rows.")

        # 4. Remove duplicates based on (flyer_path, see_more_link, label, product_name, store)
        seen = set()
        unique_rows = []
        for row in rows:
            label         = row[0]
            flyer_path    = row[1]
            product_name  = row[2]
            see_more_link = row[13]
            store         = row[14]

            # Adjust your deduplication key as needed
            # Using a more robust key including product name and store
            dedup_key = (flyer_path, see_more_link, label, product_name, store)
            if dedup_key not in seen:
                seen.add(dedup_key)
                unique_rows.append(row)
        print(f"Found {len(unique_rows)} unique items on sale.")

        if not unique_rows:
             print("No unique items found on sale for the specified period.")
             return

        # 5. Prepare data for the LLM
        # Build a prompt listing the items on sale
        items_list = []
        for row in unique_rows:
            label         = row[0]
            product_name  = row[2]
            savings       = row[4] if row[4] else "N/A" # Handle None savings
            current_price = row[5] if row[5] else "N/A" # Handle None price
            see_more_link = row[13] if row[13] else "N/A" # Handle None link
            store         = row[14]
            items_list.append(f"{label}: {product_name} - ${current_price}, save {savings}, link: {see_more_link}, store: {store}")

        # Construct the final prompt string manually
        prompt = (
            "I have the following items on sale from now until next Friday:\n\n"
            + "\n".join(items_list)
            + "\n\nCould you suggest what groceries I should buy and why?"
            + "\nPlease prioritize items based on value (savings/price) and usefulness."
            + "\nMake sure to include the **links to the items** at the end and mention the store they are from."
            + "-------- ITEMS that are higher priority include \n\n"
            + "Golden Pompano Fish, Silk, Garlic, Tomatoes, Pasta, SkyFlakes"
            + "Pork tenderloin, Blueberries, Strawberries, Bananas, Oranges, SkyFlakes crackers, Pork tenderloin, Short Ribs"
            + "Ground Pork, Chicken Wings, Cereal, Bread, Coconut Bread, Sunflower Seeds, Sunflower Seeds"
            + "Chicken Breast, Pokemon Snacks, Kettle Chips"
        )

        # 6. Call the LLM using agno Agent
        print("\nInitializing Agno Agent with Gemini model...")
        # Using Google AI Studio authentication (requires GOOGLE_API_KEY env var)
        # Using gemini-1.5-flash as recommended, but you can change to "gemini-2.0-flash"
        # Note: Ensure the model ID you use is available via Google AI Studio API Key
        gemini_model = Gemini(id="gemini-1.5-flash") # Or "gemini-2.0-flash" if preferred/available

        agent = Agent(
            model=gemini_model,
            markdown=True, # Request markdown formatting in the response
            # Optional: Add a system prompt/description if desired
            # description="You are a helpful assistant suggesting grocery purchases based on sales."
        )

        print("Sending request to Gemini model...")
        # Use agent.run() to get the response as a string
        response = agent.run(prompt)

        # Print the recommendation from the LLM
        print("\n=== Grocery Recommendations ===")
        print(response)
        print("===============================")
        import markdown
        # save markdown as html to file
        with open("grocery_recommendations.html", "a", errors="ignore", encoding="utf-8") as f:
            # convert response to html
            html_response = markdown.markdown(response)
            f.write(html_response)

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        # Catch other potential errors (e.g., network issues with LLM)
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close cursor/connection if open
        print("\nClosing database connection.")
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
