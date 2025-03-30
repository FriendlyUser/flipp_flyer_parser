import os
import datetime
import psycopg2
import openai
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
load_dotenv()

def init_llm():

    twitter_prompt = PromptTemplate(
            input_variables=["items_list"],
            template="""
            I have the following items on sale from now until next Friday:

            {items_list}
            
            Could you suggest what groceries I should buy and why? Make sure to include the links to the items.
            
        """
    )

    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

    llm = GoogleGenerativeAI(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY)
    composed_chain = twitter_prompt | llm
    return composed_chain

def main():
    # 1. Load environment variables
    load_dotenv()

    # Retrieve database URL and OpenAI API key from environment
    connection_url = os.getenv("DATABASE_URL")

    # 2. Connect to PostgreSQL
    try:
        conn = psycopg2.connect(connection_url)
        cursor = conn.cursor()

        # 3. Query rows for date range [today, next Friday]
        today = datetime.date.today()
        # Next Friday calculation
        # Monday=0, Tuesday=1, ... Sunday=6, so Friday=4
        days_until_friday = (4 - today.weekday()) % 7
        next_friday = today + datetime.timedelta(days=days_until_friday)

        query = """
            SELECT 
                label,
                flyer_path,
                product_name,
                data_product_id,
                savings,
                current_price,
                start_date,
                end_date,
                description,
                size,
                quantity,
                product_type,
                frozen,
                see_more_link,
                store
            FROM grocery
            -- Items whose sale period overlaps [today, next_friday]
            WHERE start_date <= %s
              AND end_date >= %s 
              AND store != 'saveon'
        """
        cursor.execute(query, (next_friday, today))
        rows = cursor.fetchall()

        # 4. Remove duplicates based on (flyer_path, see_more_link, label)
        seen = set()
        unique_rows = []
        for row in rows:
            label         = row[0]
            flyer_path    = row[1]
            product_name  = row[2]
            see_more_link = row[13]
            store = row[14]

            # Adjust your deduplication key as needed
            dedup_key = (flyer_path, see_more_link, label, product_name, store)
            if dedup_key not in seen:
                seen.add(dedup_key)
                unique_rows.append(row)
        
        # 5. Call an LLM with the filtered items
        # Build a prompt listing the items on sale
        items_list = []
        for row in unique_rows:
            label         = row[0]
            product_name  = row[2]
            savings       = row[4]
            current_price = row[5]
            see_more_link = row[13]
            store = row[14]
            items_list.append(f"{label}: {product_name} - ${current_price}, save {savings}, link: {see_more_link}, store {store}")

        prompt = (
            "I have the following items on sale from now until next Friday:\n"
            + "\n".join(items_list)
            + "\n\nCould you suggest what groceries I should buy and why?"
            + "\nMake sure to include the **links to the items** at the end and mention the store they are from."
            + "-------- ITEMS that are higher priority include \n\n"
            + "Golden Pompano Fish, Silk, Garlic, Tomatoes, Pasta, SkyFlakes"
            + "Pork tenderloin, Blueberries, Strawberries, Bananas, Oranges, Pork Side Ribs, Pork Back Ribs, Short Ribs"
            + "Ground Pork, Chicken Wings, Cereal, Bread, Coconut Bread, Sunflower Seeds, Sunflower Seeds"
            + "Chicken Breast, Pokemon Snacks, Kettle Chips"
        )

        # Make an OpenAI ChatCompletion request
        chain = init_llm()

        response = chain.invoke(prompt)

        # Print the recommendation from the LLM
        print("=== Grocery Recommendations ===")
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
    finally:
        # Close cursor/connection if open
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()
