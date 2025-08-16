// FCS Simulator - Main JavaScript
class FCSSimulator {
    constructor() {
        this.radarCanvas = document.getElementById('radarCanvas');
        this.ctx = this.radarCanvas.getContext('2d');
        this.radarRange = 10; // km
        this.targets = [];
        this.selectedTarget = null;
        this.isLocked = false;
        this.radarAngle = 0;
        this.isPaused = false;
        
        // turret state
        this.turretAzimuth = 0;
        this.turretElevation = 0;
        this.roundsLeft = 10;
        this.reloadReady = true;
        this.reloadCooldownMs = 2500;
        this.lastShotAt = 0;
        
        // trajectory rendering cache
        this.trajectoryPoints = [];
        
        // Ammunition properties
        this.ammoTypes = {
            'apfsds': { velocity: 1750, drag: 0.92, weight: 8.5 },
            'heat': { velocity: 1140, drag: 0.85, weight: 15.0 },
            'he': { velocity: 900, drag: 0.80, weight: 23.0 },
            'smoke': { velocity: 700, drag: 0.75, weight: 18.0 }
        };
        
        this.init();
    }
    
    init() {
        this.updateClock();
        setInterval(() => this.updateClock(), 1000);
        
        this.setupRadar();
        this.generateTargets();
        this.animate();
        
        // Initialize event listeners
        this.setupEventListeners();
    }
    
    updateClock() {
        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0];
        const dateStr = now.toISOString().split('T')[0].replace(/-/g, '.');
        
        document.getElementById('system-clock').textContent = timeStr;
        document.getElementById('system-date').textContent = dateStr;
    }
    
    setupRadar() {
        // Set canvas size
        this.radarCanvas.width = 400;
        this.radarCanvas.height = 400;
    }
    
    generateTargets() {
        // Generate random targets
        const targetTypes = ['TANK', 'APC', 'HELICOPTER', 'DRONE', 'VEHICLE'];
        
        for (let i = 0; i < 5; i++) {
            const angle = Math.random() * Math.PI * 2;
            const distance = Math.random() * this.radarRange * 0.8 + 1;
            const speed = Math.random() * 30 + 10; // m/s
            const heading = Math.random() * Math.PI * 2;
            
            this.targets.push({
                id: `TGT-${String(i + 1).padStart(3, '0')}`,
                type: targetTypes[Math.floor(Math.random() * targetTypes.length)],
                x: Math.cos(angle) * distance,
                y: Math.sin(angle) * distance,
                distance: distance,
                bearing: angle * 180 / Math.PI,
                elevation: Math.random() * 30 - 15,
                speed: speed,
                heading: heading,
                threat: Math.random() * 100
            });
        }
    }
    
    drawRadar() {
        const centerX = this.radarCanvas.width / 2;
        const centerY = this.radarCanvas.height / 2;
        const radius = 180;
        
        // Clear canvas
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        this.ctx.fillRect(0, 0, this.radarCanvas.width, this.radarCanvas.height);
        
        // Draw radar circles
        this.ctx.strokeStyle = 'rgba(0, 255, 65, 0.3)';
        this.ctx.lineWidth = 1;
        
        for (let i = 1; i <= 4; i++) {
            this.ctx.beginPath();
            this.ctx.arc(centerX, centerY, radius * i / 4, 0, Math.PI * 2);
            this.ctx.stroke();
        }
        
        // Draw radar lines
        for (let i = 0; i < 8; i++) {
            const angle = (Math.PI * 2 * i) / 8;
            this.ctx.beginPath();
            this.ctx.moveTo(centerX, centerY);
            this.ctx.lineTo(
                centerX + Math.cos(angle) * radius,
                centerY + Math.sin(angle) * radius
            );
            this.ctx.stroke();
        }
        
        // Draw sweep line
        this.ctx.strokeStyle = 'rgba(0, 255, 65, 0.8)';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, centerY);
        this.ctx.lineTo(
            centerX + Math.cos(this.radarAngle) * radius,
            centerY + Math.sin(this.radarAngle) * radius
        );
        this.ctx.stroke();
        
        // Draw sweep trail
        const gradient = this.ctx.createLinearGradient(
            centerX, centerY,
            centerX + Math.cos(this.radarAngle - 0.5) * radius,
            centerY + Math.sin(this.radarAngle - 0.5) * radius
        );
        gradient.addColorStop(0, 'rgba(0, 255, 65, 0)');
        gradient.addColorStop(1, 'rgba(0, 255, 65, 0.2)');
        
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, centerY);
        this.ctx.arc(centerX, centerY, radius, this.radarAngle - 0.5, this.radarAngle, false);
        this.ctx.closePath();
        this.ctx.fill();
        
        // Draw targets
        this.targets.forEach(target => {
            const targetX = centerX + (target.x / this.radarRange) * radius;
            const targetY = centerY + (target.y / this.radarRange) * radius;
            
            // Check if target is in radar range
            if (Math.sqrt(target.x * target.x + target.y * target.y) <= this.radarRange) {
                // Target dot
                if (target === this.selectedTarget) {
                    this.ctx.fillStyle = this.isLocked ? '#ff6b6b' : '#ffff00';
                    this.ctx.strokeStyle = this.isLocked ? '#ff6b6b' : '#ffff00';
                    
                    // Draw selection box
                    this.ctx.lineWidth = 2;
                    this.ctx.strokeRect(targetX - 10, targetY - 10, 20, 20);
                } else {
                    this.ctx.fillStyle = '#00ff41';
                }
                
                this.ctx.beginPath();
                this.ctx.arc(targetX, targetY, 4, 0, Math.PI * 2);
                this.ctx.fill();
                
                // Target label
                this.ctx.font = '10px Courier New';
                this.ctx.fillText(target.id, targetX + 8, targetY - 8);
                
                // Movement vector
                const vectorLength = 20;
                const vectorX = Math.cos(target.heading) * vectorLength;
                const vectorY = Math.sin(target.heading) * vectorLength;
                
                this.ctx.strokeStyle = 'rgba(0, 255, 65, 0.5)';
                this.ctx.lineWidth = 1;
                this.ctx.beginPath();
                this.ctx.moveTo(targetX, targetY);
                this.ctx.lineTo(targetX + vectorX, targetY + vectorY);
                this.ctx.stroke();
            }
        });
        
        // Draw turret direction
        this.drawTurret(centerX, centerY, radius);
        
        // Draw trajectory if opted-in
        const showTraj = document.getElementById('show-traj');
        if (showTraj && showTraj.checked && this.trajectoryPoints.length > 1) {
            this.ctx.strokeStyle = 'rgba(0, 191, 255, 0.8)';
            this.ctx.lineWidth = 1;
            this.ctx.beginPath();
            for (let i = 0; i < this.trajectoryPoints.length - 1; i++) {
                const p = this.trajectoryPoints[i];
                const n = this.trajectoryPoints[i + 1];
                this.ctx.moveTo(centerX + (p.x / this.radarRange) * radius, centerY + (p.y / this.radarRange) * radius);
                this.ctx.lineTo(centerX + (n.x / this.radarRange) * radius, centerY + (n.y / this.radarRange) * radius);
            }
            this.ctx.stroke();
        }
        
        // Update radar angle
        this.radarAngle += 0.05;
        if (this.radarAngle > Math.PI * 2) {
            this.radarAngle = 0;
        }
    }
    
    updateTargets() {
        this.targets.forEach(target => {
            // Update target position based on speed and heading
            const deltaX = Math.cos(target.heading) * target.speed * 0.001; // Convert to km
            const deltaY = Math.sin(target.heading) * target.speed * 0.001;
            
            target.x += deltaX * 0.1; // Slow down for visualization
            target.y += deltaY * 0.1;
            
            // Update distance and bearing
            target.distance = Math.sqrt(target.x * target.x + target.y * target.y);
            target.bearing = Math.atan2(target.y, target.x) * 180 / Math.PI;
            
            // Random heading changes
            if (Math.random() < 0.01) {
                target.heading += (Math.random() - 0.5) * 0.5;
            }
            
            // Update threat level based on distance and type
            const baseThreat = {
                'TANK': 80,
                'APC': 60,
                'HELICOPTER': 70,
                'DRONE': 40,
                'VEHICLE': 30
            };
            
            target.threat = baseThreat[target.type] * (1 - target.distance / this.radarRange / 2);
        });
    }
    
    animate() {
        if (!this.isPaused) {
            this.drawRadar();
            this.updateTargets();
            if (this.selectedTarget) {
                this.updateTargetInfo();
            }
        } else {
            this.drawRadar();
            if (this.selectedTarget) {
                this.updateTargetInfo();
            }
        }
        requestAnimationFrame(() => this.animate());
    }
    
    updateTargetInfo() {
        const target = this.selectedTarget;
        
        document.getElementById('target-id').textContent = target.id;
        document.getElementById('target-distance').textContent = `${(target.distance * 1000).toFixed(0)} m`;
        document.getElementById('target-bearing').textContent = `${target.bearing.toFixed(1)}°`;
        document.getElementById('target-elevation').textContent = `${target.elevation.toFixed(1)}°`;
        document.getElementById('target-speed').textContent = `${target.speed.toFixed(1)} m/s`;
        document.getElementById('target-type').textContent = target.type;
        
        // Update threat level
        const threatLevel = document.getElementById('threat-level');
        const threatText = document.getElementById('threat-text');
        
        threatLevel.style.width = `${target.threat}%`;
        
        if (target.threat > 70) {
            threatLevel.style.background = 'linear-gradient(90deg, #ff6b6b, #ff0000)';
            threatText.textContent = 'HIGH THREAT';
            threatText.style.color = '#ff6b6b';
        } else if (target.threat > 40) {
            threatLevel.style.background = 'linear-gradient(90deg, #ffff00, #ff6b6b)';
            threatText.textContent = 'MEDIUM THREAT';
            threatText.style.color = '#ffff00';
        } else {
            threatLevel.style.background = 'linear-gradient(90deg, #00ff41, #ffff00)';
            threatText.textContent = 'LOW THREAT';
            threatText.style.color = '#00ff41';
        }
    }
    
    calculateBallisticSolution() {
        if (!this.selectedTarget) {
            this.addLogEntry('ERROR: No target selected');
            return;
        }
        const autoCalc = document.getElementById('auto-calc');
        const target = this.selectedTarget;
        const ammoType = document.getElementById('ammo-type').value;
        const windSpeed = parseFloat(document.getElementById('wind-speed').value);
        const windDir = parseFloat(document.getElementById('wind-dir').value);
        const temperature = parseFloat(document.getElementById('temperature').value);
        const ammo = this.ammoTypes[ammoType];
        const distance = target.distance * 1000; // m
        const gravity = 9.81;
        // Approximate air density (unused but placeholder for future drag model)
        const airDensity = 1.225 * (1 - temperature * 0.0065 / 288.15);
        // Time-to-target including simple closure due to target motion along line-of-sight
        const losBearingRad = Math.atan2(target.y, target.x);
        const targetClosure = target.speed * Math.cos(target.heading - losBearingRad);
        const effectiveDistance = Math.max(1, distance + targetClosure * (distance / ammo.velocity));
        const timeToTarget = effectiveDistance / ammo.velocity;
        // Elevation
        const dropCompensation = 0.5 * gravity * Math.pow(timeToTarget, 2);
        const elevationRad = Math.atan(dropCompensation / effectiveDistance);
        const elevation = elevationRad * 180 / Math.PI + target.elevation;
        // Lead
        const targetVelocityX = Math.cos(target.heading) * target.speed;
        const targetVelocityY = Math.sin(target.heading) * target.speed;
        const leadDistance = Math.hypot(targetVelocityX * timeToTarget, targetVelocityY * timeToTarget);
        const leadAngle = Math.atan2(targetVelocityY * timeToTarget, effectiveDistance + targetVelocityX * timeToTarget) * 180 / Math.PI;
        // Wind compensation (very simplified)
        const windCompensation = (windSpeed * timeToTarget / Math.max(1, effectiveDistance)) * Math.sin((windDir - target.bearing) * Math.PI / 180) * 180 / Math.PI;
        // Final
        const azimuth = target.bearing + leadAngle + windCompensation;
        const leadMils = (leadDistance / Math.max(1, effectiveDistance)) * 1000;
        // Update display
        document.getElementById('solution-azimuth').textContent = `${azimuth.toFixed(2)}°`;
        document.getElementById('solution-elevation').textContent = `${elevation.toFixed(2)}°`;
        document.getElementById('solution-lead').textContent = `${leadMils.toFixed(1)} mils`;
        document.getElementById('solution-time').textContent = `${timeToTarget.toFixed(2)} s`;
        // Update turret desired state and trajectory preview
        this.turretAzimuth = azimuth;
        this.turretElevation = elevation;
        this.updateWeaponStatus();
        this.trajectoryPoints = this.simulateTrajectoryPoints(ammo.velocity, elevationRad, timeToTarget, target);
        this.addLogEntry(`Ballistic solution calculated for ${target.id}`);
        this.addLogEntry(`Ammo: ${ammoType.toUpperCase()}, Distance: ${distance.toFixed(0)}m`);
        if (this.isLocked) {
            document.querySelector('.action-btn.fire').disabled = false;
        }
    }
    
    setupEventListeners() {
        // Radar canvas click to select target
        this.radarCanvas.addEventListener('click', (e) => {
            const rect = this.radarCanvas.getBoundingClientRect();
            const x = e.clientX - rect.left - 200; // Center X
            const y = e.clientY - rect.top - 200; // Center Y
            
            // Find closest target
            let closestTarget = null;
            let closestDistance = Infinity;
            
            this.targets.forEach(target => {
                const targetX = (target.x / this.radarRange) * 180;
                const targetY = (target.y / this.radarRange) * 180;
                const distance = Math.sqrt(
                    Math.pow(x - targetX, 2) + Math.pow(y - targetY, 2)
                );
                
                if (distance < 20 && distance < closestDistance) {
                    closestDistance = distance;
                    closestTarget = target;
                }
            });
            
            if (closestTarget) {
                this.selectedTarget = closestTarget;
                this.isLocked = false;
                document.querySelector('.action-btn.fire').disabled = true;
                this.addLogEntry(`Target ${closestTarget.id} selected`);
                if (document.getElementById('auto-calc')?.checked) {
                    this.calculateBallisticSolution();
                }
            }
        });
        // auto recalc on parameter change
        const autoRecalc = () => {
            if (this.selectedTarget && document.getElementById('auto-calc')?.checked) {
                this.calculateBallisticSolution();
            }
        };
        ['ammo-type','wind-speed','wind-dir','temperature'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('change', autoRecalc);
                el.addEventListener('input', autoRecalc);
            }
        });
        // keyboard shortcuts
        window.addEventListener('keydown', (e) => {
            if (e.key === ' ') { e.preventDefault(); togglePause(); }
            if (e.key.toLowerCase() === 'a') { acquireTarget(); }
            if (e.key.toLowerCase() === 'l') { lockTarget(); }
            if (e.key.toLowerCase() === 'f') { fireWeapon(); }
            if (e.key.toLowerCase() === 'c') { calculateSolution(); }
        });
    }
    
    addLogEntry(message) {
        const logContent = document.getElementById('system-log');
        const timestamp = new Date().toTimeString().split(' ')[0];
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.textContent = `[${timestamp}] ${message}`;
        logContent.appendChild(entry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    drawTurret(centerX, centerY, radius) {
        // represent turret pointing direction
        const azRad = this.turretAzimuth * Math.PI / 180;
        this.ctx.strokeStyle = 'rgba(255, 255, 0, 0.8)';
        this.ctx.lineWidth = 1.5;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, centerY);
        this.ctx.lineTo(centerX + Math.cos(azRad) * radius, centerY + Math.sin(azRad) * radius);
        this.ctx.stroke();
    }

    updateWeaponStatus() {
        const az = document.getElementById('turret-az');
        const el = document.getElementById('turret-el');
        const reload = document.getElementById('reload-status');
        const rounds = document.getElementById('rounds-left');
        if (az) az.textContent = `${this.turretAzimuth.toFixed(1)}°`;
        if (el) el.textContent = `${this.turretElevation.toFixed(1)}°`;
        if (reload) reload.textContent = this.reloadReady ? 'READY' : 'RELOADING';
        if (rounds) rounds.textContent = `${this.roundsLeft}`;
    }

    simulateTrajectoryPoints(muzzleVelocity, elevationRad, timeToTarget, target) {
        const dt = 0.05; // s
        const g = 9.81;
        const points = [];
        // initial position in km space, convert to km for radar overlay
        let x0 = 0; let y0 = 0;
        // Convert to km per second
        const vx = (muzzleVelocity * Math.cos(elevationRad)) / 1000;
        const vy = (muzzleVelocity * Math.sin(elevationRad)) / 1000;
        // project in bearing direction towards target bearing
        const bearingRad = (this.turretAzimuth) * Math.PI / 180;
        let px = 0; let py = 0; let t = 0;
        while (t <= timeToTarget) {
            const dx = vx * t; // km
            const dy = vy * t - 0.5 * g * t * t / 1000; // km (since g is m/s^2)
            px = Math.cos(bearingRad) * dx - Math.sin(bearingRad) * 0 + 0;
            py = Math.sin(bearingRad) * dx + Math.cos(bearingRad) * 0 + 0;
            points.push({ x: px, y: py + dy });
            t += dt;
        }
        return points;
    }
}

// Global functions for button actions
let fcs;

window.onload = () => {
    fcs = new FCSSimulator();
};

function togglePause() {
    fcs.isPaused = !fcs.isPaused;
    const btn = document.getElementById('btn-pause');
    if (btn) btn.textContent = fcs.isPaused ? 'RESUME' : 'PAUSE';
    fcs.addLogEntry(fcs.isPaused ? 'Simulation paused' : 'Simulation resumed');
}

function resetScenario() {
    fcs.targets = [];
    fcs.selectedTarget = null;
    fcs.isLocked = false;
    fcs.roundsLeft = 10;
    fcs.reloadReady = true;
    fcs.trajectoryPoints = [];
    document.querySelector('.action-btn.fire').disabled = true;
    document.getElementById('target-id').textContent = '---';
    document.getElementById('target-distance').textContent = '--- m';
    document.getElementById('target-bearing').textContent = '---°';
    document.getElementById('target-elevation').textContent = '---°';
    document.getElementById('target-speed').textContent = '--- m/s';
    document.getElementById('target-type').textContent = '---';
    fcs.generateTargets();
    fcs.addLogEntry('Scenario reset');
    fcs.updateWeaponStatus();
}

function exportLog() {
    const logContent = document.getElementById('system-log');
    const lines = Array.from(logContent.querySelectorAll('.log-entry')).map(e => e.textContent).join('\n');
    const blob = new Blob([lines], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fcs_log_${new Date().toISOString().replace(/[:.]/g,'-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function changeRadarRange(delta) {
    fcs.radarRange = Math.max(5, Math.min(50, fcs.radarRange + delta));
    document.getElementById('radar-range').textContent = fcs.radarRange;
    fcs.addLogEntry(`Radar range changed to ${fcs.radarRange} km`);
}

function acquireTarget() {
    if (fcs.targets.length > 0) {
        // Find highest threat target
        let highestThreat = fcs.targets[0];
        fcs.targets.forEach(target => {
            if (target.threat > highestThreat.threat) {
                highestThreat = target;
            }
        });
        
        fcs.selectedTarget = highestThreat;
        fcs.isLocked = false;
        document.querySelector('.action-btn.fire').disabled = true;
        fcs.addLogEntry(`Auto-acquired highest threat: ${highestThreat.id}`);
    } else {
        fcs.addLogEntry('No targets available');
    }
}

function calculateSolution() {
    fcs.calculateBallisticSolution();
}

function lockTarget() {
    if (!fcs.selectedTarget) {
        fcs.addLogEntry('ERROR: No target selected');
        return;
    }
    
    fcs.isLocked = true;
    fcs.addLogEntry(`Target ${fcs.selectedTarget.id} LOCKED`);
    
    // Calculate solution automatically
    fcs.calculateBallisticSolution();
}

function fireWeapon() {
    if (!fcs.isLocked || !fcs.selectedTarget) {
        fcs.addLogEntry('ERROR: No locked target');
        return;
    }
    if (!fcs.reloadReady) {
        fcs.addLogEntry('RELOAD IN PROGRESS');
        return;
    }
    if (fcs.roundsLeft <= 0) {
        fcs.addLogEntry('NO ROUNDS LEFT');
        return;
    }
    fcs.roundsLeft -= 1;
    fcs.reloadReady = false;
    fcs.lastShotAt = Date.now();
    fcs.updateWeaponStatus();
    const ammoType = document.getElementById('ammo-type').value;
    fcs.addLogEntry(`FIRING ${ammoType.toUpperCase()} at ${fcs.selectedTarget.id}`);
    if (document.getElementById('sound-on')?.checked) {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const o = ctx.createOscillator();
            const g = ctx.createGain();
            o.type = 'square';
            o.frequency.value = 220; g.gain.value = 0.05;
            o.connect(g); g.connect(ctx.destination);
            o.start(); setTimeout(() => { o.stop(); ctx.close(); }, 120);
        } catch (_) {}
    }
    // Simulate firing effect
    document.querySelector('.action-btn.fire').style.background = '#ff0000';
    setTimeout(() => {
        document.querySelector('.action-btn.fire').style.background = '';
    }, 500);
    // Simulate hit probability
    const hitChance = Math.random();
    const distance = fcs.selectedTarget.distance * 1000;
    const hitProbability = Math.max(0.3, 1 - distance / 5000);
    setTimeout(() => {
        if (hitChance < hitProbability) {
            fcs.addLogEntry(`TARGET HIT! ${fcs.selectedTarget.id} destroyed`);
            const index = fcs.targets.indexOf(fcs.selectedTarget);
            if (index > -1) {
                fcs.targets.splice(index, 1);
            }
            fcs.selectedTarget = null;
            fcs.isLocked = false;
            document.querySelector('.action-btn.fire').disabled = true;
            fcs.trajectoryPoints = [];
            document.getElementById('target-id').textContent = '---';
            document.getElementById('target-distance').textContent = '--- m';
            document.getElementById('target-bearing').textContent = '---°';
            document.getElementById('target-elevation').textContent = '---°';
            document.getElementById('target-speed').textContent = '--- m/s';
            document.getElementById('target-type').textContent = '---';
        } else {
            fcs.addLogEntry(`MISS! Recalculating...`);
            fcs.calculateBallisticSolution();
        }
    }, 2000);
    // start reload timer
    setTimeout(() => {
        fcs.reloadReady = true;
        fcs.updateWeaponStatus();
        fcs.addLogEntry('Reload complete');
    }, fcs.reloadCooldownMs);
}