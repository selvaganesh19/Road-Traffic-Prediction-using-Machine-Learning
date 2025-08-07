from flask import Flask, request, jsonify, send_from_directory
import numpy as np
import flask_cors
import os
import pickle
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import io
import base64

app = Flask(__name__, static_folder='../frontend')
flask_cors.CORS(app)

# Global variables
pkl_model = None
model_info = {}
prediction_history = []

def load_traffic_model():
    """Load traffic prediction model"""
    global pkl_model, model_info
    
    model_files = ['traffic_predictor.joblib', 'traffic_model.joblib', 'model.joblib', 'traffic_predictor.pkl', 'model.pkl']
    
    for model_file in model_files:
        model_path = os.path.join(os.path.dirname(__file__), model_file)
        if os.path.exists(model_path):
            try:
                pkl_model = joblib.load(model_path) if model_file.endswith('.joblib') else pickle.load(open(model_path, 'rb'))
                file_size = os.path.getsize(model_path) / (1024 * 1024)
                model_info = {'file_name': model_file, 'file_size_mb': file_size, 'model_type': str(type(pkl_model))}
                print(f"✅ Model loaded: {model_file} ({file_size:.2f} MB)")
                return True
            except Exception as e:
                print(f"❌ Failed to load {model_file}: {e}")
    
    print("❌ No valid model found")
    return False

def encode_input_for_model(day_of_week, season, location):
    """Encode inputs for model prediction"""
    mappings = {
        'day': {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6},
        'season': {'spring': 0, 'summer': 1, 'autumn': 2, 'winter': 3},
        'location': {'east': 0, 'west': 1, 'north': 2, 'south': 3}
    }
    
    day_encoded = mappings['day'].get(day_of_week.lower(), 0)
    season_encoded = mappings['season'].get(season.lower(), 0)
    location_encoded = mappings['location'].get(location.lower(), 0)
    is_weekend = 1 if day_of_week.lower() in ['saturday', 'sunday'] else 0
    
    # Create 9-feature array
    features = [day_encoded, season_encoded, location_encoded, is_weekend, 1, 0, 1, season_encoded * 3 + 6, 25.0]
    
    # Try different formats
    feature_names_options = [
        ['day_of_week', 'season', 'location', 'is_weekend', 'hour_morning', 'hour_evening', 'weather', 'month', 'temperature'],
        ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9']
    ]
    
    formats = [np.array([features])]
    for names in feature_names_options:
        try:
            formats.append(pd.DataFrame([features], columns=names))
        except:
            pass
    
    return formats

def create_hourly_pattern(base_traffic, day_of_week, season, location):
    """Create realistic hourly traffic pattern"""
    patterns = {6: 0.4, 7: 0.8, 8: 1.2, 9: 1.0, 10: 0.7, 12: 0.8, 14: 0.6, 16: 0.9, 17: 1.3, 18: 1.5, 19: 1.1, 20: 0.8, 22: 0.5}
    
    multipliers = {
        'day': {'monday': 1.1, 'tuesday': 1.0, 'wednesday': 1.0, 'thursday': 1.0, 'friday': 1.2, 'saturday': 0.8, 'sunday': 0.7},
        'season': {'spring': 1.0, 'summer': 1.1, 'autumn': 0.9, 'winter': 0.8},
        'location': {'east': 1.2, 'west': 1.1, 'north': 0.9, 'south': 1.0}
    }
    
    day_mult = multipliers['day'].get(day_of_week.lower(), 1.0)
    season_mult = multipliers['season'].get(season.lower(), 1.0)
    location_mult = multipliers['location'].get(location.lower(), 1.0)
    
    results = []
    for hour, pattern in patterns.items():
        traffic = base_traffic * pattern * day_mult * season_mult * location_mult
        level = 'light' if traffic < 30 else 'moderate' if traffic < 60 else 'high' if traffic < 90 else 'heavy'
        
        results.append({
            'hour': hour,
            'traffic_level': level,
            'is_peak': hour in [7, 8, 9, 17, 18, 19],
            'raw_prediction': traffic
        })
    
    return results

def predict_full_day_traffic(day_of_week, season, location):
    """Main prediction function"""
    if not pkl_model:
        return create_fallback_prediction(day_of_week, season, location)
    
    try:
        encoded_formats = encode_input_for_model(day_of_week, season, location)
        
        for encoded_input in encoded_formats:
            try:
                if hasattr(pkl_model, 'predict'):
                    predictions = pkl_model.predict(encoded_input)
                elif hasattr(pkl_model, 'predict_proba'):
                    predictions = pkl_model.predict_proba(encoded_input)
                else:
                    continue
                
                # Process predictions
                pred_array = np.array(predictions).flatten()
                
                if len(pred_array) == 1:
                    # Single class prediction
                    predicted_class = int(pred_array[0])
                    base_traffic = {0: 25, 1: 50, 2: 75, 3: 100}.get(predicted_class, 50)
                elif len(pred_array) == 4:
                    # 4 class probabilities
                    base_traffic = (np.argmax(pred_array) + 1) * 25
                else:
                    base_traffic = 50
                
                results = create_hourly_pattern(base_traffic, day_of_week, season, location)
                save_to_history(day_of_week, season, location, results)
                return results
                
            except Exception:
                continue
        
        # If all formats fail, use fallback
        return create_fallback_prediction(day_of_week, season, location)
        
    except Exception:
        return create_fallback_prediction(day_of_week, season, location)

def create_fallback_prediction(day_of_week, season, location):
    """Enhanced fallback prediction"""
    base_patterns = {'monday': 65, 'tuesday': 52, 'wednesday': 58, 'thursday': 55, 'friday': 78, 'saturday': 42, 'sunday': 38}
    season_vars = {'spring': 5, 'summer': 8, 'autumn': -3, 'winter': -8}
    location_vars = {'east': 12, 'west': 8, 'north': -5, 'south': 2}
    
    base_traffic = base_patterns.get(day_of_week.lower(), 50)
    base_traffic += season_vars.get(season.lower(), 0) + location_vars.get(location.lower(), 0)
    
    # Add consistent randomness
    import random
    random.seed(hash(f"{day_of_week}{season}{location}"))
    base_traffic += random.randint(-10, 10)
    
    return create_hourly_pattern(base_traffic, day_of_week, season, location)

def save_to_history(day_of_week, season, location, results):
    """Save prediction to history"""
    history_entry = {
        'timestamp': datetime.now().isoformat(),
        'input_features': {'day_of_week': day_of_week, 'season': season, 'location': location},
        'hourly_predictions': results,
        'peak_hours': [r['hour'] for r in results if r['is_peak']],
        'heavy_traffic_hours': [r['hour'] for r in results if r['traffic_level'] == 'heavy']
    }
    
    prediction_history.append(history_entry)
    if len(prediction_history) > 50:
        prediction_history.pop(0)

def generate_graphs():
    """Generate traffic analysis graphs"""
    try:
        fig = plt.figure(figsize=(16, 12))
        
        # Use sample data if no history
        if len(prediction_history) < 5:
            sample_data = []
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            seasons = ['spring', 'summer', 'autumn', 'winter']
            locations = ['east', 'west', 'north', 'south']
            
            for i in range(15):
                hourly_predictions = create_hourly_pattern(50 + (i % 30), days[i % 7], seasons[i % 4], locations[i % 4])
                sample_data.append({
                    'input_features': {'day_of_week': days[i % 7], 'season': seasons[i % 4], 'location': locations[i % 4]},
                    'hourly_predictions': hourly_predictions,
                    'peak_hours': [h['hour'] for h in hourly_predictions if h['is_peak']],
                    'heavy_traffic_hours': [h['hour'] for h in hourly_predictions if h['traffic_level'] == 'heavy']
                })
        else:
            sample_data = prediction_history[-20:]
        
        # 1. Traffic by Hour
        plt.subplot(2, 3, 1)
        hours, traffic_levels = [], []
        for entry in sample_data:
            for hourly in entry['hourly_predictions']:
                hours.append(hourly['hour'])
                traffic_levels.append(hourly['raw_prediction'])
        
        if hours:
            plt.scatter(hours, traffic_levels, alpha=0.6, c='blue')
            plt.title('Traffic Distribution by Hour', fontweight='bold')
            plt.xlabel('Hour of Day')
            plt.ylabel('Traffic Level')
            plt.grid(True, alpha=0.3)
        
        # 2. Peak Hours Analysis
        plt.subplot(2, 3, 2)
        peak_hours_count = {}
        for entry in sample_data:
            for hour in entry.get('peak_hours', []):
                peak_hours_count[hour] = peak_hours_count.get(hour, 0) + 1
        
        if peak_hours_count:
            plt.bar(list(peak_hours_count.keys()), list(peak_hours_count.values()), color='orange', alpha=0.7)
            plt.title('Peak Hours Frequency', fontweight='bold')
            plt.xlabel('Hour')
            plt.ylabel('Frequency')
        
        # 3-6. Other graphs (Location, Day, Season, Heavy Traffic)
        graph_configs = [
            ('location', 'Location', ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99']),
            ('day_of_week', 'Day of Week', 'lightblue'),
            ('season', 'Season', ['#FFB6C1', '#98FB98', '#DDA0DD', '#F0E68C']),
        ]
        
        for i, (key, title, colors) in enumerate(graph_configs, 3):
            plt.subplot(2, 3, i)
            data = {}
            for entry in sample_data:
                val = entry['input_features'][key]
                if val not in data:
                    data[val] = []
                avg_traffic = np.mean([h['raw_prediction'] for h in entry['hourly_predictions']])
                data[val].append(avg_traffic)
            
            if data:
                keys = list(data.keys())
                avg_values = [np.mean(data[k]) for k in keys]
                color = colors if isinstance(colors, list) else [colors] * len(keys)
                plt.bar(keys, avg_values, color=color[:len(keys)], alpha=0.8)
                plt.title(f'Average Traffic by {title}', fontweight='bold')
                plt.xlabel(title)
                plt.ylabel('Average Traffic Level')
                if title == 'Day of Week':
                    plt.xticks(rotation=45)
        
        # 6. Heavy Traffic Hours
        plt.subplot(2, 3, 6)
        heavy_hours = {}
        for entry in sample_data:
            for hour in entry.get('heavy_traffic_hours', []):
                heavy_hours[hour] = heavy_hours.get(hour, 0) + 1
        
        if heavy_hours:
            plt.bar(list(heavy_hours.keys()), list(heavy_hours.values()), color='red', alpha=0.7)
            plt.title('Heavy Traffic Hours', fontweight='bold')
            plt.xlabel('Hour')
            plt.ylabel('Frequency')
        
        plt.tight_layout()
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return img_base64
        
    except Exception as e:
        print(f"❌ Graph generation failed: {e}")
        return None

# Initialize model
print("🚀 Starting Traffic Prediction Server...")
load_traffic_model()


@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'model_loaded': pkl_model is not None,
        'model_info': model_info,
        'prediction_method': 'ML Model' if pkl_model else 'Fallback',
        'prediction_history_count': len(prediction_history),
        'available_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'available_seasons': ['Spring', 'Summer', 'Autumn', 'Winter'],
        'available_locations': ['East', 'West', 'North', 'South']
    })

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error="No input data provided")
        
        day_of_week = data.get('day_of_week', 'Monday')
        season = data.get('season', 'Spring')
        location = data.get('location', 'East')
        
        predictions = predict_full_day_traffic(day_of_week, season, location)
        
        if predictions:
            return jsonify(
                success=True,
                prediction={
                    'day_of_week': day_of_week,
                    'season': season,
                    'location': location,
                    'hourly_predictions': predictions,
                    'total_hours': len(predictions),
                    'peak_hours': [p['hour'] for p in predictions if p['is_peak']],
                    'heavy_traffic_hours': [p['hour'] for p in predictions if p['traffic_level'] == 'heavy']
                },
                model_used='ML Model' if pkl_model else 'Fallback'
            )
        else:
            return jsonify(success=False, error="Prediction failed")
        
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/analytics-dashboard')
def analytics_dashboard():
    try:
        if len(prediction_history) > 0:
            recent = prediction_history[-10:]
            days = [p['input_features']['day_of_week'] for p in recent]
            seasons = [p['input_features']['season'] for p in recent]
            locations = [p['input_features']['location'] for p in recent]
            
            all_peak_hours = []
            all_heavy_hours = []
            for p in recent:
                all_peak_hours.extend(p.get('peak_hours', []))
                all_heavy_hours.extend(p.get('heavy_traffic_hours', []))
            
            analytics = {
                'total_predictions': len(prediction_history),
                'most_common_day': max(set(days), key=days.count) if days else 'N/A',
                'most_common_season': max(set(seasons), key=seasons.count) if seasons else 'N/A',
                'most_common_location': max(set(locations), key=locations.count) if locations else 'N/A',
                'most_common_peak_hour': max(set(all_peak_hours), key=all_peak_hours.count) if all_peak_hours else 'N/A',
                'most_common_heavy_hour': max(set(all_heavy_hours), key=all_heavy_hours.count) if all_heavy_hours else 'N/A'
            }
        else:
            analytics = {'message': 'No prediction history available', 'total_predictions': 0}
        
        return jsonify({'success': True, 'analytics': analytics, 'model_info': model_info, 'timestamp': datetime.now().isoformat()})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/graphs')
def get_graphs():
    try:
        graph_base64 = generate_graphs()
        if graph_base64:
            return jsonify({
                'success': True,
                'graph_data': graph_base64,
                'prediction_count': len(prediction_history),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to generate graphs'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚦 TRAFFIC PREDICTION SERVER")
    print("🌐 http://localhost:5000")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=5000)