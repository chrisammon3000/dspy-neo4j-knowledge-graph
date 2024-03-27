import json
import neo4j

def parse_relationships(schema: dict) -> str:
    # Parse the JSON string into a Python object if it's not already
    if isinstance(schema, str):
        data = json.loads(schema)
    else:
        data = schema
    
    data = data[0]['relationships']
    
    # Initialize a list to hold the formatted relationship strings
    relationships = []
    
    # Iterate through each relationship in the data
    for relationship in data:
        entity1, relation, entity2 = relationship
        # Extract the names of the entities and the relationship
        entity1_name = entity1['name']
        entity2_name = entity2['name']
        # Format the string as specified and add it to the list
        formatted_relationship = f"{entity1_name}-{relation}->{entity2_name}"
        relationships.append(formatted_relationship)
    
    # Join all formatted strings with a newline character
    result = "\n".join(relationships)
    return result

def parse_nodes(schema):
    schema = schema
    nodes = [node['name'] for node in schema[0]['nodes']]
    return "\n".join(nodes)

class Neo4j:
    def __init__(self, uri, user: str = None, password: str = None):
        self._uri = uri
        self._user = user
        self._password = password
        self._auth = None if (self._user is None and self._password is None) else (self._user, self._password)
        self._driver = neo4j.GraphDatabase.driver(self._uri, auth=(self._user, self._password))

        self._verify_connection()

    def close(self):
        self._driver.close()

    def _verify_connection(self):
        with self._driver as driver:
            driver.verify_connectivity()

    def query(self, query, parameters=None, db=None):
        assert db is None, "The Neo4j implementation does not support multiple databases."
        with self._driver.session(database=db) as session:
            result = session.run(query, parameters)
            return result.data()

    def schema(self, parsed=False):
        query = """
        CALL db.schema.visualization()
        """
        schema = self.query(query)
        
        if parsed:
            return parse_nodes(schema), parse_relationships(schema)
        
        return schema
    
