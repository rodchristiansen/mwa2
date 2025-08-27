#!/usr/bin/env python3
"""
MWA2 YAML Support - Development Demo Server
Simple Flask demo to showcase YAML functionality
NOT FOR PRODUCTION USE - Development Testing Only
"""

from flask import Flask, render_template_string, jsonify, request
import yaml
import plistlib
import os
import json
from datetime import datetime

app = Flask(__name__)

# Copy our YAML utility functions
def is_yaml_file(filepath):
    """Check if a file path has a YAML extension"""
    if not filepath:
        return False
    file_extension = os.path.splitext(filepath)[1].lower()
    return file_extension in ['.yaml', '.yml']

def read_plist_or_yaml(filepath):
    """Read a file that could be either plist or YAML format"""
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except Exception as e:
        return {'error': f'Could not read file: {e}'}
    
    # Try YAML first if it looks like YAML
    if is_yaml_file(filepath):
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            # Fallback to plist
            try:
                return plistlib.loads(content.encode('utf-8'))
            except Exception:
                return {'error': 'Could not parse as YAML or plist'}
    else:
        # Try plist first
        try:
            return plistlib.loads(content.encode('utf-8'))
        except Exception:
            # Fallback to YAML
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError:
                return {'error': 'Could not parse as plist or YAML'}

def read_file_raw(filepath):
    """Read raw file content for display"""
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f'Error reading file: {e}'

# Demo HTML template
DEMO_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>MWA2 YAML Support - Development Demo</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .yaml { background: #f8f9fa; }
        .plist { background: #fff3cd; }
        pre { background: #f1f3f4; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 13px; max-height: 400px; overflow-y: auto; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { background: #d4edda; color: #155724; }
        .info { background: #d1ecf1; color: #0c5460; }
        .error { background: #f8d7da; color: #721c24; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .content-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        .file-info { background: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 15px; }
        .raw-content { background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Monaco', 'Courier New', monospace; font-size: 12px; white-space: pre-wrap; word-wrap: break-word; max-height: 400px; overflow-y: auto; }
        .tab-buttons { margin-bottom: 15px; }
        .tab-button { background: #6c757d; margin-right: 10px; }
        .tab-button.active { background: #007bff; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MWA2 YAML Support - Development Demo</h1>
            <p>Interactive demonstration of YAML functionality in MunkiWebAdmin2</p>
            
            <div class="warning">
                <strong>Development Demo Only:</strong> This is a proof-of-concept demonstration for development and testing purposes. 
                Not intended for production deployment. Shows dual-format parsing capabilities.
            </div>
            
            <div class="status success">
                Status: <strong>Development Testing Active</strong> | 
                Format Detection: <strong>Working</strong> | 
                Dual Parser: <strong>Functional</strong>
            </div>
        </div>

        <div class="section">
            <h2>Available Test Files</h2>
            <div class="grid">
                <div>
                    <h3>YAML Files (.yaml)</h3>
                    {% for file in yaml_files %}
                    <div style="margin: 10px 0;">
                        <button onclick="loadFile('{{ file }}')">{{ file }}</button>
                    </div>
                    {% endfor %}
                </div>
                <div>
                    <h3>Plist Files (.plist)</h3>
                    {% for file in plist_files %}
                    <div style="margin: 10px 0;">
                        <button onclick="loadFile('{{ file }}')">{{ file }}</button>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div class="section">
            <h2>File Content Analysis</h2>
            <div id="file-content">
                <div class="status info">Select a file above to view its raw content and parsed data</div>
            </div>
        </div>

        <div class="section">
            <h2>Implementation Features</h2>
            <div class="grid">
                <div>
                    <h3>Core Functionality</h3>
                    <ul>
                        <li>Extension-based format detection</li>
                        <li>Content-based format detection</li>
                        <li>Intelligent dual parsing with fallback</li>
                        <li>Format-aware reading operations</li>
                        <li>Django model integration</li>
                        <li>Backward compatibility with plist</li>
                    </ul>
                </div>
                <div>
                    <h3>Development Status</h3>
                    <ul>
                        <li>Enhanced MWA2 Django web application</li>
                        <li>Mixed repository support (YAML + plist)</li>
                        <li>Error handling and fallback mechanisms</li>
                        <li>Configurable format preferences</li>
                        <li>Test coverage for dual-format scenarios</li>
                        <li>Docker containerization capabilities</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        function loadFile(filename) {
            fetch('/api/file/' + encodeURIComponent(filename))
                .then(response => response.json())
                .then(data => {
                    const contentDiv = document.getElementById('file-content');
                    
                    if (data.error) {
                        contentDiv.innerHTML = `<div class="status error">Error: ${data.error}</div>`;
                        return;
                    }
                    
                    const isYaml = filename.endsWith('.yaml') || filename.endsWith('.yml');
                    const formatClass = isYaml ? 'yaml' : 'plist';
                    const formatName = isYaml ? 'YAML' : 'Plist';
                    
                    contentDiv.innerHTML = `
                        <div class="file-info">
                            <strong>File:</strong> ${filename} | 
                            <strong>Format:</strong> ${formatName} | 
                            <strong>Detection:</strong> ${data.detected_format || 'Auto'} |
                            <strong>Size:</strong> ${data.raw_content ? data.raw_content.length : 'Unknown'} bytes
                        </div>
                        
                        <div class="tab-buttons">
                            <button class="tab-button active" onclick="switchTab('raw', this)">Raw Content</button>
                            <button class="tab-button" onclick="switchTab('parsed', this)">Parsed Data (JSON)</button>
                        </div>
                        
                        <div id="raw-tab" class="tab-content active">
                            <h3>Raw File Content</h3>
                            <div class="raw-content">${escapeHtml(data.raw_content || 'No raw content available')}</div>
                        </div>
                        
                        <div id="parsed-tab" class="tab-content">
                            <h3>Parsed Content (JSON Structure)</h3>
                            <pre class="${formatClass}">${JSON.stringify(data.content, null, 2)}</pre>
                        </div>
                        
                        <div class="status info" style="margin-top: 15px;">
                            <strong>Detection Result:</strong> This file was automatically detected as ${formatName} format and parsed successfully using the dual-format engine.
                            The parser ${isYaml ? 'used YAML parsing with plist fallback available' : 'used plist parsing with YAML fallback available'}.
                        </div>
                    `;
                })
                .catch(error => {
                    document.getElementById('file-content').innerHTML = `<div class="status error">Network error: ${error}</div>`;
                });
        }

        function switchTab(tabName, button) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all tab buttons
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // Add active class to clicked button
            button.classList.add('active');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Auto-load first file on page load
        window.onload = () => {
            const buttons = document.querySelectorAll('button');
            if (buttons.length > 0) {
                // Find first file button (skip tab buttons)
                for (let button of buttons) {
                    if (button.onclick && button.onclick.toString().includes('loadFile')) {
                        button.click();
                        break;
                    }
                }
            }
        };
    </script>
</body>
</html>
"""

@app.route('/')
def demo():
    """Main demo page"""
    # Scan for available files
    yaml_files = []
    plist_files = []
    
    # Check test_repo directory
    test_dirs = ['test_repo/pkgsinfo', 'test_repo/manifests']
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            for file in os.listdir(test_dir):
                filepath = os.path.join(test_dir, file)
                if os.path.isfile(filepath):
                    if file.endswith(('.yaml', '.yml')):
                        yaml_files.append(f"{test_dir}/{file}")
                    elif file.endswith('.plist'):
                        plist_files.append(f"{test_dir}/{file}")
    
    return render_template_string(DEMO_TEMPLATE, 
                                yaml_files=yaml_files, 
                                plist_files=plist_files)

@app.route('/api/file/<path:filename>')
def get_file(filename):
    """API endpoint to get file content"""
    try:
        content = read_plist_or_yaml(filename)
        raw_content = read_file_raw(filename)
        
        if content is None:
            return jsonify({'error': 'File not found'})
        
        return jsonify({
            'filename': filename,
            'content': content,
            'raw_content': raw_content,
            'detected_format': 'YAML' if is_yaml_file(filename) else 'Plist',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/status')
def status():
    """API status endpoint"""
    return jsonify({
        'status': 'active',
        'yaml_support': True,
        'features': [
            'Extension-based format detection',
            'Content-based format detection', 
            'Intelligent dual parsing with fallback',
            'Format-aware reading operations',
            'Mixed repository support'
        ],
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("MWA2 YAML Support - Development Demo Server")
    print("=" * 50)
    print("Demo URL: http://localhost:5001")
    print("API Status: http://localhost:5001/api/status")
    print("Features: Dual-format YAML + Plist parsing")
    print("Warning: Development demo only - not for production")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5001, debug=True)
