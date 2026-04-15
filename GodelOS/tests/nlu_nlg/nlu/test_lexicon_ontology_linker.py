"""
Unit tests for the LexiconOntologyLinker module.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.nlu_nlg.nlu.lexical_analyzer_parser import Token
from godelOS.nlu_nlg.nlu.lexicon_ontology_linker import (
    LexiconOntologyLinker, Lexicon, Ontology, LexicalEntry, OntologyConcept,
    WordNetLexicon
)


class TestLexiconOntologyLinker(unittest.TestCase):
    """Test cases for the LexiconOntologyLinker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock for WordNet
        self.wordnet_patcher = patch('godelOS.nlu_nlg.nlu.lexicon_ontology_linker.wn')
        self.mock_wordnet = self.wordnet_patcher.start()
        
        # Create a mock for NLTK data
        self.nltk_data_patcher = patch('godelOS.nlu_nlg.nlu.lexicon_ontology_linker.nltk.data')
        self.mock_nltk_data = self.nltk_data_patcher.start()
        self.mock_nltk_data.find.return_value = True  # Pretend resources are available
        
        # Create a mock for NLTK download
        self.nltk_download_patcher = patch('godelOS.nlu_nlg.nlu.lexicon_ontology_linker.nltk.download')
        self.mock_nltk_download = self.nltk_download_patcher.start()
        
        # Create a custom lexicon and ontology for testing
        self.lexicon = Lexicon()
        self.ontology = Ontology()
        
        # Populate the lexicon and ontology with test data
        self._populate_test_data()
        
        # Create the lexicon-ontology linker
        self.linker = LexiconOntologyLinker(self.lexicon, self.ontology)
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.wordnet_patcher.stop()
        self.nltk_data_patcher.stop()
        self.nltk_download_patcher.stop()
    
    def _populate_test_data(self):
        """Populate the lexicon and ontology with test data."""
        # Create lexical entries
        dog_entry = LexicalEntry(
            lemma="dog",
            pos="NOUN",
            senses=["dog.n.01"],
            synonyms=["canine", "hound"],
            hypernyms=["animal", "mammal"],
            hyponyms=["poodle", "terrier"]
        )
        
        cat_entry = LexicalEntry(
            lemma="cat",
            pos="NOUN",
            senses=["cat.n.01"],
            synonyms=["feline"],
            hypernyms=["animal", "mammal"],
            hyponyms=["tabby", "siamese"]
        )
        
        run_entry = LexicalEntry(
            lemma="run",
            pos="VERB",
            senses=["run.v.01"],
            synonyms=["jog", "sprint"],
            hypernyms=["move"]
        )
        
        # Add entries to the lexicon
        self.lexicon.add_entry(dog_entry)
        self.lexicon.add_entry(cat_entry)
        self.lexicon.add_entry(run_entry)
        
        # Create ontology concepts
        entity_concept = OntologyConcept(
            id="entity",
            name="Entity",
            description="The root concept"
        )
        
        animal_concept = OntologyConcept(
            id="animal",
            name="Animal",
            description="A living organism",
            parent_concepts=["entity"],
            lexical_mappings=["animal"]
        )
        
        dog_concept = OntologyConcept(
            id="dog",
            name="Dog",
            description="A domestic canine",
            parent_concepts=["animal"],
            lexical_mappings=["dog", "canine", "hound"]
        )
        
        cat_concept = OntologyConcept(
            id="cat",
            name="Cat",
            description="A domestic feline",
            parent_concepts=["animal"],
            lexical_mappings=["cat", "feline"]
        )
        
        # Add concepts to the ontology
        self.ontology.add_concept(entity_concept)
        self.ontology.add_concept(animal_concept)
        self.ontology.add_concept(dog_concept)
        self.ontology.add_concept(cat_concept)
        
        # Add mappings from lexical entries to ontology concepts
        dog_entry.ontology_mappings["dog.n.01"] = "dog"
        cat_entry.ontology_mappings["cat.n.01"] = "cat"
    
    def test_link_term_to_concept(self):
        """Test linking a term to an ontology concept."""
        # Create a token for "dog"
        dog_token = Token(
            text="dog", lemma="dog", pos="NOUN", tag="NN", dep="nsubj",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=0, i=0
        )
        
        # Link the token to a concept
        concept = self.linker.link_term_to_concept(dog_token)
        
        # Check that the concept was found
        self.assertIsNotNone(concept)
        self.assertEqual(concept.id, "dog")
        self.assertEqual(concept.name, "Dog")
    
    def test_link_term_to_concept_with_synonym(self):
        """Test linking a term to an ontology concept using a synonym."""
        # Create a token for "canine"
        canine_token = Token(
            text="canine", lemma="canine", pos="NOUN", tag="NN", dep="nsubj",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=0, i=0
        )
        
        # Link the token to a concept
        concept = self.linker.link_term_to_concept(canine_token)
        
        # Check that the concept was found
        self.assertIsNotNone(concept)
        self.assertEqual(concept.id, "dog")
        self.assertEqual(concept.name, "Dog")
    
    def test_link_term_to_concept_not_found(self):
        """Test linking a term that doesn't map to any concept."""
        # Create a token for "computer"
        computer_token = Token(
            text="computer", lemma="computer", pos="NOUN", tag="NN", dep="nsubj",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=0, i=0
        )
        
        # Link the token to a concept
        concept = self.linker.link_term_to_concept(computer_token)
        
        # Check that no concept was found
        self.assertIsNone(concept)
    
    def test_disambiguate_sense(self):
        """Test disambiguating the sense of a word."""
        # Create a token for "dog"
        dog_token = Token(
            text="dog", lemma="dog", pos="NOUN", tag="NN", dep="nsubj",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=0, i=0
        )
        
        # Get the lexical entry
        entry = self.lexicon.get_entry("dog", "NOUN")
        
        # Disambiguate the sense
        sense = self.linker.disambiguate_sense(dog_token, entry)
        
        # Check that a sense was returned
        self.assertIsNotNone(sense)
        self.assertEqual(sense, "dog.n.01")
    
    def test_get_concept_hierarchy(self):
        """Test getting the hierarchy of a concept."""
        # Get the "dog" concept
        dog_concept = self.ontology.get_concept("dog")
        
        # Get the hierarchy
        hierarchy = self.linker.get_concept_hierarchy(dog_concept)
        
        # Check that the hierarchy is correct
        self.assertEqual(hierarchy["id"], "dog")
        self.assertEqual(hierarchy["name"], "Dog")
        self.assertEqual(len(hierarchy["parents"]), 1)
        self.assertEqual(hierarchy["parents"][0]["id"], "animal")
    
    def test_get_lexical_relations(self):
        """Test getting the lexical relations of a word."""
        # Create a token for "dog"
        dog_token = Token(
            text="dog", lemma="dog", pos="NOUN", tag="NN", dep="nsubj",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=0, i=0
        )
        
        # Get the lexical relations
        relations = self.linker.get_lexical_relations(dog_token)
        
        # Check that the relations are correct
        self.assertEqual(set(relations["synonyms"]), {"canine", "hound"})
        self.assertEqual(set(relations["hypernyms"]), {"animal", "mammal"})
        self.assertEqual(set(relations["hyponyms"]), {"poodle", "terrier"})
    
    def test_add_mapping(self):
        """Test adding a mapping from a lexical sense to an ontology concept."""
        # Add a mapping for "run.v.01" to a new concept
        self.linker.add_mapping("run", "VERB", "run.v.01", "entity")
        
        # Check that the mapping was added
        entry = self.lexicon.get_entry("run", "VERB")
        self.assertIsNotNone(entry)
        self.assertIn("run.v.01", entry.ontology_mappings)
        self.assertEqual(entry.ontology_mappings["run.v.01"], "entity")
        
        # Check that the concept was updated
        concept = self.ontology.get_concept("entity")
        self.assertIsNotNone(concept)
        self.assertIn("run", concept.lexical_mappings)


class TestWordNetLexicon(unittest.TestCase):
    """Test cases for the WordNetLexicon class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock for WordNet
        self.wordnet_patcher = patch('godelOS.nlu_nlg.nlu.lexicon_ontology_linker.wn')
        self.mock_wordnet = self.wordnet_patcher.start()
        
        # Set up WordNet constants
        self.mock_wordnet.NOUN = 'n'
        self.mock_wordnet.VERB = 'v'
        self.mock_wordnet.ADJ = 'a'
        self.mock_wordnet.ADV = 'r'
        
        # Create a mock for NLTK data
        self.nltk_data_patcher = patch('godelOS.nlu_nlg.nlu.lexicon_ontology_linker.nltk.data')
        self.mock_nltk_data = self.nltk_data_patcher.start()
        self.mock_nltk_data.find.return_value = True  # Pretend resources are available
        
        # Create a mock for NLTK download
        self.nltk_download_patcher = patch('godelOS.nlu_nlg.nlu.lexicon_ontology_linker.nltk.download')
        self.mock_nltk_download = self.nltk_download_patcher.start()
        
        # Create the WordNet lexicon
        self.lexicon = WordNetLexicon()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.wordnet_patcher.stop()
        self.nltk_data_patcher.stop()
        self.nltk_download_patcher.stop()
    
    def test_get_entry_from_wordnet(self):
        """Test getting a lexical entry from WordNet."""
        # Set up a mock synset
        mock_synset = MagicMock()
        mock_synset.name.return_value = "dog.n.01"
        mock_synset.examples.return_value = ["The dog barked."]
        
        # Set up a mock lemma
        mock_lemma = MagicMock()
        mock_lemma.name.return_value = "dog"
        mock_lemma.antonyms.return_value = []
        
        # Set up another mock lemma for synonyms
        mock_synonym_lemma = MagicMock()
        mock_synonym_lemma.name.return_value = "canine"
        mock_synonym_lemma.antonyms.return_value = []
        
        # Set up the synset's lemmas
        mock_synset.lemmas.return_value = [mock_lemma, mock_synonym_lemma]
        
        # Set up a mock hypernym synset
        mock_hypernym = MagicMock()
        mock_hypernym_lemma = MagicMock()
        mock_hypernym_lemma.name.return_value = "animal"
        mock_hypernym.lemmas.return_value = [mock_hypernym_lemma]
        
        # Set up a mock hyponym synset
        mock_hyponym = MagicMock()
        mock_hyponym_lemma = MagicMock()
        mock_hyponym_lemma.name.return_value = "poodle"
        mock_hyponym.lemmas.return_value = [mock_hyponym_lemma]
        
        # Set up the synset's hypernyms and hyponyms
        mock_synset.hypernyms.return_value = [mock_hypernym]
        mock_synset.hyponyms.return_value = [mock_hyponym]
        mock_synset.part_meronyms.return_value = []
        mock_synset.substance_meronyms.return_value = []
        mock_synset.part_holonyms.return_value = []
        mock_synset.substance_holonyms.return_value = []
        
        # Configure the mock WordNet to return the mock synset
        self.mock_wordnet.synsets.return_value = [mock_synset]
        
        # Get the entry
        entry = self.lexicon.get_entry("dog", "NOUN")
        
        # Check that the entry was created correctly
        self.assertIsNotNone(entry)
        self.assertEqual(entry.lemma, "dog")
        self.assertEqual(entry.pos, "NOUN")
        self.assertIn("dog.n.01", entry.senses)
        self.assertIn("canine", entry.synonyms)
        self.assertIn("animal", entry.hypernyms)
        self.assertIn("poodle", entry.hyponyms)
    
    def test_map_pos_to_wordnet(self):
        """Test mapping POS tags to WordNet POS."""
        # Test direct mappings
        self.assertEqual(self.lexicon._map_pos_to_wordnet("NOUN"), 'n')
        self.assertEqual(self.lexicon._map_pos_to_wordnet("VERB"), 'v')
        self.assertEqual(self.lexicon._map_pos_to_wordnet("ADJ"), 'a')
        self.assertEqual(self.lexicon._map_pos_to_wordnet("ADV"), 'r')
        
        # Test prefix mappings
        self.assertEqual(self.lexicon._map_pos_to_wordnet("NN"), 'n')
        self.assertEqual(self.lexicon._map_pos_to_wordnet("VB"), 'v')
        self.assertEqual(self.lexicon._map_pos_to_wordnet("JJ"), 'a')
        self.assertEqual(self.lexicon._map_pos_to_wordnet("RB"), 'r')
        
        # Test unknown POS
        self.assertIsNone(self.lexicon._map_pos_to_wordnet("X"))


if __name__ == '__main__':
    unittest.main()