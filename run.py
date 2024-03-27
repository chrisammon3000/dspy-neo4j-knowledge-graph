"""
Text -> Knowledge Graph
1. text -> cypher

Constraints:
- Use the existing schema before creating new nodes and relationships.
"""
import os
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv());
import dspy
from src.neo4j import Neo4j

# set up Neo4j using NEO4J_URI
neo4j = Neo4j(uri=os.getenv("NEO4J_URI"), user=os.getenv("NEO4J_USER"), password=os.getenv("NEO4J_PASSWORD"))

def fmt_schema(neo4j: Neo4j):
    parsed = neo4j.schema(parsed=True)
    return "\n".join([f"{element}:\n{parsed[idx]}\n" for idx, element in enumerate(["NODES", "RELATIONSHIPS"])])

lm = dspy.OpenAI(
    model="gpt-4",
    max_tokens=500,
)
dspy.configure(lm=lm)

class CypherFromText(dspy.Signature):
    """Create a Cypher MERGE statement to model all entities and relationships found in the text."""

    text = dspy.InputField(desc="Text to model.")
    statement = dspy.OutputField(desc="Cypher statement to merge nodes and relationships found in the text.")

generate_cypher = dspy.ChainOfThought(CypherFromText)

if __name__ == "__main__":
    # text = "The quick brown fox jumps over the lazy dog."
    # text = 'John Singer Sargent (/ˈsɑːrdʒənt/; January 12, 1856 – April 14, 1925)[1] was an American expatriate artist, considered the "leading portrait painter of his generation" for his evocations of Edwardian-era luxury.[2][3] He created roughly 900 oil paintings and more than 2,000 watercolors, as well as countless sketches and charcoal drawings. His oeuvre documents worldwide travel, from Venice to the Tyrol, Corfu, Spain, the Middle East, Montana, Maine, and Florida.'
    
    text = input("Enter text: ")
    cypher = generate_cypher(text=text)
    neo4j.query(cypher.statement.replace('```', ''))
    print()