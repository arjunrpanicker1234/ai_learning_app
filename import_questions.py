import csv
from app import create_app, db  # Import the app factory and db
from models import Question, Skill

# Create the Flask app instance using the factory function
app = create_app()

# CSV file path (make sure this file exists in your project folder)
CSV_FILE = 'static/data/questions.csv'

# Function to import questions from CSV
def import_questions_from_csv(csv_file):
    with app.app_context():  # Access the Flask app context to interact with the database
        with open(csv_file, 'r') as file:
            csv_reader = csv.DictReader(file)

            for row in csv_reader:
                skill_name = row['skill_name']
                question_text = row['question_text']
                option1 = row['option1']
                option2 = row['option2']
                option3 = row['option3']
                option4 = row['option4']
                correct_option = int(row['correct_option'])
                difficulty = int(row['difficulty'])

                # Find the skill by name
                skill = Skill.query.filter_by(name=skill_name).first()

                if skill:  # If skill exists, create the question
                    question = Question(
                        skill_id=skill.id,
                        question_text=question_text,
                        option1=option1,
                        option2=option2,
                        option3=option3,
                        option4=option4,
                        correct_option=correct_option,
                        difficulty=difficulty,
                    )

                    db.session.add(question)
                    print(f"Added question: '{question_text}' under skill: {skill_name}")
                else:
                    print(f"Skill '{skill_name}' not found. Skipping question: '{question_text}'.")

            # Commit all added questions to the database
            db.session.commit()
            print("Questions successfully imported from CSV!")

# Import questions from CSV
import_questions_from_csv(CSV_FILE)
