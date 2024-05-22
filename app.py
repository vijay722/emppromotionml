from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pandas as pd

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Read data from CSV
data = pd.read_csv("employee_data.csv")

# Assuming the model expects 7 features, adjust the data accordingly
# Example: adding a new feature called 'new_feature' with default value 0
data['new_feature'] = 0

# Split data into features (X) and target variable (y)
X = data.drop("is_promoted", axis=1)  # Features
y = data["is_promoted"]  # Target variable

# Identify categorical columns
categorical_columns = ["department", "region", "education", "gender", "recruitment_channel"]

# Convert categorical columns to numerical representations using one-hot encoding
X_encoded = pd.get_dummies(X, columns=categorical_columns)

# Standardize numerical columns
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_encoded)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Train the model
model = DecisionTreeClassifier()
model.fit(X_train, y_train)

# Function to predict promotion based on employee details
def predict_promotion(employee_details):
    # Convert input to DataFrame with proper column names
    employee_df = pd.DataFrame.from_dict(employee_details, orient='index').T
    
    # Convert categorical columns to numerical representations using one-hot encoding
    employee_encoded = pd.get_dummies(employee_df, columns=categorical_columns)
    
    # Reorder columns to match the order during model training
    employee_encoded = employee_encoded.reindex(columns=X_encoded.columns, fill_value=0)
    
    # Standardize numerical columns using the same scaler used during training
    scaled_features = scaler.transform(employee_encoded)
    
    # Predict promotion
    prediction = model.predict(scaled_features)
    return prediction[0]  # Return 1 for promoted, 0 for not promoted

# Route for the home page (index)
@app.route("/")
def index():
    recent_promotions = session.get('recent_promotions', [])
    manager_message = session.get('manager_message', "")  # Retrieve manager message
    return render_template("index.html", recent_promotions=recent_promotions, manager_message=manager_message)

# Route for login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Check username and password
        if username == "admin" and password == "admin":
            session['logged_in'] = True
            return redirect(url_for("employee_dashboard"))
        elif username == "manager" and password == "manager":  # Add manager login credentials
            session['manager_logged_in'] = True
            return redirect(url_for("manager_dashboard"))
        else:
            flash("Invalid username or password")
            
    return render_template("login.html")

# Route for employee dashboard
@app.route("/employee_dashboard", methods=["GET", "POST"])
def employee_dashboard():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))

    # Retrieve all employee submissions from the session
    employee_submissions = session.get('employee_submissions', [])

    if request.method == "POST":
        # Get employee details from the form
        employee_id = request.form.get("employee_id")
        employee_name = request.form.get("employee_name")
        department = request.form.get("department")
        region = request.form.get("region")
        education = request.form.get("education")
        gender = request.form.get("gender")
        recruitment_channel = request.form.get("recruitment_channel")
        no_of_trainings = request.form.get("no_of_trainings")
        age = request.form.get("age")
        previous_year_rating = request.form.get("previous_year_rating")
        length_of_service = request.form.get("length_of_service")
        awards_won = request.form.get("awards_won")
        avg_training_score = request.form.get("avg_training_score")

        # Create an employee_details dictionary
        employee_details = {
            'employee_id': employee_id,
            'employee_name': employee_name,
            'department': department,
            'region': region,
            'education': education,
            'gender': gender,
            'recruitment_channel': recruitment_channel,
            'no_of_trainings': no_of_trainings,
            'age': age,
            'previous_year_rating': previous_year_rating,
            'length_of_service': length_of_service,
            'awards_won': awards_won,
            'avg_training_score': avg_training_score
        }

        # Predict promotion
        promotion_status = predict_promotion(employee_details)
        response_message = f"Congratulations, {employee_name} ({employee_id})! You will be promoted." if promotion_status == 1 else f"Sorry, {employee_name} ({employee_id}), you will not be promoted this time."
        
        # Append the new submission to the list of all employee submissions
        employee_submissions.append({"employee_id": employee_id, "message": response_message})
        
        # Store all employee submissions in session
        session['employee_submissions'] = employee_submissions
        
        # Update recent employee form fields in session
        recent_employee_fields = session.get('recent_employee_fields', [])
        recent_employee_fields.append({
            'employee_id': employee_id,
            'employee_name': employee_name,
            'promotion_status': "Promoted" if promotion_status == 1 else "Not Promoted"
        })
        session['recent_employee_fields'] = recent_employee_fields
        
        # Store promotion status in recent promotions (for manager)
        recent_promotions = session.get('recent_promotions', [])
        recent_promotions.append({"employee_id": employee_id, "promotion_status": "Promoted" if promotion_status == 1 else "Not Promoted"})
        session['recent_promotions'] = recent_promotions

        return jsonify({"message": response_message})

    return render_template("employee_dashboard.html", employee_submissions=employee_submissions)

# Route for manager dashboard
@app.route("/manager_dashboard", methods=["GET", "POST"])
def manager_dashboard():
    if 'manager_logged_in' not in session or not session['manager_logged_in']:
        return redirect(url_for('login'))

    # Retrieve recent employee form fields from session
    recent_employee_fields = session.get('recent_employee_fields', [])

    if request.method == "POST":
        # Retrieve message from the form
        message = request.form.get("message")

        # Store message in session
        session['manager_message'] = message

        return redirect(url_for('manager_dashboard'))

    return render_template("manager_dashboard.html", recent_employee_fields=recent_employee_fields)

# Route for sending messages (send_message)
@app.route("/send_message", methods=["POST"])
def send_message():
    # Retrieve message from the form
    message = request.form.get("message")

    # Store message in session
    session['manager_message'] = message

    # Redirect to the index page
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
