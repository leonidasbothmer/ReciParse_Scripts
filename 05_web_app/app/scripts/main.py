from flask import Flask, render_template, url_for, request
from flaskext.markdown import Markdown

import typer

# Importing NLP Stuff
import spacy
from spacy import displacy

# import 
# New Tokenizer

# For Rel Model
# from scripts import rel_pipe
# from scripts import rel_model
# from scripts import custom_functions

import rel_pipe
import rel_model
import custom_functions
# Load Models
# Cocos paths
#ner_nlp = spacy.load(r"C:\Users\CocoL\Universität St.Gallen\STUD-Capstoneproject Tell 6 - General\02-Coding\03-Models\NER trained on nightly\ner-cb1-159-15-12")
# rel_nlp = spacy.load(r"C:\Users\CocoL\Universität St.Gallen\STUD-Capstoneproject Tell 6 - General\02-Coding\03-Models\Relations\0-trained-on-djx\model-best")
#rel_nlp = spacy.load(r"C:\Users\CocoL\Universität St.Gallen\STUD-Capstoneproject Tell 6 - General\02-Coding\04-performance\rel-trf-01_04-coco\training\model-best")

# rel_nlp = spacy.load(r"C:\Users\CocoL\Universität St.Gallen\STUD-Capstoneproject Tell 6 - General\02-Coding\03-Models\Relations\16-12_relations_tok2vec")

# Leos paths
# ner_nlp = spacy.load(r"/Users/leonidas/OneDrive - Universität St.Gallen/General/02-Coding/03-Models/NER trained on nightly/ner-cb1-159-15-12")
# # rel_nlp = spacy.load(r"C:\Users\CocoL\Universität St.Gallen\STUD-Capstoneproject Tell 6 - General\02-Coding\03-Models\Relations\0-trained-on-djx\model-best")
# rel_nlp = spacy.load(r"/Users/leonidas/OneDrive - Universität St.Gallen/General/02-Coding/03-Models/Relations/16-12_relations_tok2vec")
# rel_nlp = spacy.load(r"/Users/leonidas/OneDrive - Universität St.Gallen/General/02-Coding/04-performance/rel-trf-01_04-coco/training/model-best")
#make the factory work
from rel_pipe import make_relation_extractor, score_relations

#make the config work
from rel_model import create_relation_model, create_classification_layer, create_instances, create_tensors

# Jonathans paths
ner_nlp = spacy.load(r"/Users/jonathanebner/Universität St.Gallen/STUD-Capstoneproject Tell 6 - General/02-Coding/03-Models/NER trained on nightly/ner-cb1-159-15-12")
# # rel_nlp = spacy.load(r"C:\Users\CocoL\Universität St.Gallen\STUD-Capstoneproject Tell 6 - General\02-Coding\03-Models\Relations\0-trained-on-djx\model-best")
rel_nlp = spacy.load(r"/Users/jonathanebner/Universität St.Gallen/STUD-Capstoneproject Tell 6 - General/02-Coding/03-Models/Relations/16-12_relations_tok2vec")
# rel_nlp = spacy.load(r"/Users/jonathanebner/Desktop/app_transformer/model/rel_trans")
print("models loaded")


# Initialize App
app = Flask(__name__)
Markdown(app)

@app.route("/")#, methods=['GET','POST'])
def home():
    # demo_text = "Die Pinienkerne in der trockenen Pfanne goldgelb rösten und dann auf einem Teller abkühlen lassen.Die Zucchini waschen, putzen und in Scheiben schneiden. Die Champignons säubern und in mundgerechte Stücke schneiden. Die Zwiebel schälen und in kleine Würfel schneiden, den Schinken in Streifen schneiden und noch zweimal quer durchschneiden.Die Bandnudeln in reichlich Salzwasser bissfest kochen, abgießen und abtropfen lassen.Etwas Pflanzenöl in einer großen beschichteten Pfanne erhitzen und die Zwiebeln darin glasig werden lassen. Schinken und Rosmarin dazugeben und ca. 2 Minuten mit anbraten. Champignons und Zucchini in die Pfanne geben und kurz mit anbraten. Mit der Gemüsebrühe ablöschen und alles zugedeckt bei mittlerer Hitze ca. 10 Minuten dünsten. Die Sahne einrühren und die Sauce mit Salz und Pfeffer abschmecken.Die Nudeln unterheben, kurz durchschwenken, dann alles auf zwei tiefe Teller verteilen und mit Pinienkernen bestreut servieren. Dazu kann man noch frisch geriebenen Parmesan reichen."
    # docx = nlp(demo_text)

    # demo_html = displacy.render(docx, style= "ent")
    # demo_result = demo_html

    # # Just Display regular text
    # plain_text = docx.text
    return render_template("home.html")#, demo_result = demo_result, demo_text = plain_text)

@app.route("/output", methods= ["GET", "POST"])
def columns():
    if request.method == "POST":
        rawtext = request.form["rawtext"]

        # --- Spacy 3 with rel ---

        # Get NE predictions
        pred = ner_nlp(rawtext)

        # Get Relation predictions
        for name, proc in rel_nlp.pipeline:
            pred = proc(pred)

        # Extract Steps from relations
        v_list = [(ent.start, ent.text) for ent in pred.ents if ent.label_ == "V" ]
        
        ents_dict = { ent.start: ent.text for ent in pred.ents}

        threshhold = 0.05
        steps_list = []
        for v_start, v in v_list:
            step_tup = (v,{})
            for rels_tup, probs in pred._.rel.items():
                max_prob_rel = max(probs, key=probs.get)
                if rels_tup[0] == v_start and probs[max_prob_rel] > threshhold:
                    if probs[max_prob_rel] not in step_tup[1]:
                        step_tup[1][max_prob_rel] = [ents_dict[rels_tup[1]]] # doc[ent_start_i]
                    else:
                        step_tup[1][max_prob_rel].append(ents_dict[rels_tup[1]])
            steps_list.append(step_tup) 
        # print(steps_list)


        labels_dict = {
            "ArgNone": "None",
            "Arg0Z": "Zutat (S)",
            "Arg0Tool": "Tool (S)",
            "Arg1Z": "Zutat (O)",
            "Arg1Tool": "Tool (O)",
            "ArgPräp": "Präposition",
            "ArgZeitp": "Zeitpunkt",
            "ArgDauer": "Dauer",
            "ArgTemp": "Temperatur"
        }

        # --- Display NE with displacy ---
        r,g,b = "#ECC1C9", "#BCDCD0", "#C3CEEA"

        colors = {
            "V": r, 
            "Z":g, "TOOL": g, 
            "TEMP": b, "ATTR": b, "PRÄP":  b, "ZEITP": b, "DAUER": b, 
        }
            
        my_options = {"ents": ["V","Z", "TOOL", "TEMP", "ATTR","ZEITP","DAUER", "PRÄP" ], "colors": colors}
        demo_html = displacy.render(pred, style= "ent", options=my_options)
        demo_result = demo_html

        # Just Display regular text
        plain_text = pred.text

    return render_template(
        "output.html", 
        title="Output",  
        demo_result = demo_result, 
        demo_text = plain_text,
        steps_list = steps_list,
        labels_dict = labels_dict,
        ents_dict = ents_dict,
        rawtext = rawtext
        )

if __name__ == "__main__":
    app.run(debug=True)#debug=True