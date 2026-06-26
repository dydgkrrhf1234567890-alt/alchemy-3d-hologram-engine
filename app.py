#!/usr/bin/env python3
"""
app.py

Flask web application for the Solid Vision Engine.
Provides an interactive interface to generate and visualize 3D holograms.
"""

from flask import Flask, render_template, request, jsonify, send_file
from solid_vision import SolidVisionEngine
import os
import io
import base64
from PIL import Image as PILImage
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string for embedding in HTML."""
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close(fig)
    return img_base64


def generate_hologram_image(X, Y, Z, title="Solid Vision 3D Hologram", cmap="viridis", 
                           view_elev=30.0, view_azim=-60.0):
    """Generate hologram visualization and return as base64."""
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    
    surf = ax.plot_surface(X, Y, Z, cmap=cmap, linewidth=0, antialiased=False)
    
    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z (height)")
    ax.view_init(elev=view_elev, azim=view_azim)
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
    
    return fig_to_base64(fig)


@app.route('/')
def index():
    """Render the main interface."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Generate hologram from scalar parameters."""
    try:
        data = request.get_json()
        
        # Extract parameters with defaults
        resolution = int(data.get('resolution', 200))
        complexity = float(data.get('complexity', 85.0))
        resonance_freq = float(data.get('resonance_freq', 528.0))
        amplitude_scale = float(data.get('amplitude_scale', 2.0))
        base_frequency_ref = float(data.get('base_frequency_ref', 432.0))
        view_elev = float(data.get('view_elev', 30.0))
        view_azim = float(data.get('view_azim', -60.0))
        cmap = data.get('cmap', 'viridis')
        
        # Validate ranges
        resolution = max(50, min(resolution, 500))
        complexity = max(0, min(complexity, 200))
        
        # Generate hologram
        engine = SolidVisionEngine(resolution=resolution)
        X, Y, Z = engine.convert_2d_to_3d_hologram(
            image_complexity=complexity,
            resonance_freq=resonance_freq,
            amplitude_scale=amplitude_scale,
            base_frequency_ref=base_frequency_ref
        )
        
        # Generate visualization
        img_base64 = generate_hologram_image(
            X, Y, Z,
            title="Solid Vision 3D Hologram Matrix",
            cmap=cmap,
            view_elev=view_elev,
            view_azim=view_azim
        )
        
        return jsonify({
            'status': 'success',
            'image': img_base64,
            'message': '[오라클] 솔로몬의 성결 주파수 공명 완료. 3D 공간 벡터 준비 완료.'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error generating hologram: {str(e)}'
        }), 400


@app.route('/generate_from_image', methods=['POST'])
def generate_from_image():
    """Generate hologram from uploaded image."""
    try:
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({'status': 'error', 'message': 'No image provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        # Extract parameters
        resolution = int(request.form.get('resolution', 256))
        amplitude_scale = float(request.form.get('amplitude_scale', 2.0))
        base_frequency_ref = float(request.form.get('base_frequency_ref', 432.0))
        resonance_freq = float(request.form.get('resonance_freq', 528.0))
        view_elev = float(request.form.get('view_elev', 30.0))
        view_azim = float(request.form.get('view_azim', -60.0))
        cmap = request.form.get('cmap', 'viridis')
        
        # Validate ranges
        resolution = max(50, min(resolution, 500))
        
        # Save uploaded file temporarily
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                                 f"temp_{datetime.now().timestamp()}.png")
        file.save(temp_path)
        
        try:
            # Generate hologram from image
            engine = SolidVisionEngine(resolution=resolution)
            X, Y, Z = engine.convert_2d_to_3d_hologram(
                image_path=temp_path,
                resonance_freq=resonance_freq,
                amplitude_scale=amplitude_scale,
                base_frequency_ref=base_frequency_ref
            )
            
            # Generate visualization
            img_base64 = generate_hologram_image(
                X, Y, Z,
                title="Image-Based Hologram Matrix",
                cmap=cmap,
                view_elev=view_elev,
                view_azim=view_azim
            )
            
            return jsonify({
                'status': 'success',
                'image': img_base64,
                'message': '[오라클] 이미지 기반 홀로그램 생성 완료.'
            })
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error generating hologram from image: {str(e)}'
        }), 400


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
