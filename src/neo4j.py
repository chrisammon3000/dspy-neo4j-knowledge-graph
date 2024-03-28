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

def parse_node_properties(node_properties):
    # Initialize a dictionary to accumulate node details
    node_details = {}

    # Iterate through each item in the input JSON
    for item in node_properties:
        node_label = item["nodeLabels"][0]  # Assuming there's always one label
        prop_name = item["propertyName"]
        mandatory = "required" if item["mandatory"] else "optional"

        # Prepare the property string
        property_str = f"{prop_name} ({mandatory})" if item["mandatory"] else prop_name

        # If the node label exists, append the property; otherwise, create a new entry
        if node_label in node_details:
            node_details[node_label].append(property_str)
        else:
            node_details[node_label] = [property_str]

    # Format the output
    output_lines = []
    for node, properties in node_details.items():
        output_lines.append(f"{node}")
        for prop in properties:
            prop_line = f"  - {prop}" if "required" in prop else f"  - {prop}"
            output_lines.append(prop_line)

    return "\n".join(output_lines)


def parse_rel_properties(rel_properties):
    # Initialize a dictionary to accumulate relationship details
    rel_details = {}

    # Iterate through each item in the input JSON
    for item in rel_properties:
        # Extract relationship type name, removing :` and `
        rel_type = item["relType"][2:].strip("`")
        prop_name = item["propertyName"]
        mandatory = "required" if item["mandatory"] else "optional"

        # If propertyName is not None, prepare the property string
        if prop_name is not None:
            property_str = f"{prop_name} ({mandatory})"
            # If the relationship type exists, append the property; otherwise, create a new entry
            if rel_type in rel_details:
                rel_details[rel_type].append(property_str)
            else:
                rel_details[rel_type] = [property_str]
        else:
            # For relationships without properties, ensure the relationship is listed
            rel_details.setdefault(rel_type, [])

    # Format the output
    output_lines = []
    for rel_type, properties in rel_details.items():
        output_lines.append(f"{rel_type}")
        for prop in properties:
            output_lines.append(f"  - {prop}")

    return "\n".join(output_lines)


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
    
    def schema_properties(self, parsed=False):
        props = self._schema_node_properties(), self._schema_relationship_properties()
        if parsed:
            return parse_node_properties(props[0]), parse_rel_properties(props[1])
        
        return props

    def _schema_node_properties(self):
        query = """
        CALL db.schema.nodeTypeProperties()
        """
        return self.query(query)
    
    def _schema_relationship_properties(self):
        query = """
        CALL db.schema.relTypeProperties()
        """
        return self.query(query)
    
    def fmt_schema(self):
        parsed_schema = self.schema(parsed=True)
        parsed_props = self.schema_properties(parsed=True)
        parsed = (*parsed_props, parsed_schema[1])
        return "\n".join([f"{element}:\n{parsed[idx]}\n" for idx, element in enumerate(["NODE LABELS & PROPERTIES", "RELATIONSHIP LABELS & PROPERTIES", "RELATIONSHIPS"])])