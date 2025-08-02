import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import warnings

warnings.filterwarnings('ignore')


class IrrigationAnalyzer:
    def __init__(self, garden_config, sampling_data_df):
        """
        Initialize the analyzer with configuration and sampling data

        Args:
            config_json: Dictionary containing sensors, vegetables, gardens, and mappings
            sampling_data_df: DataFrame with columns: ['timestamp', 'sensor_id', 'sensor_type', 'value']
        """

        self.df = sampling_data_df
        self.gardens = garden_config['gardens']
        self.vegetables = garden_config['vegetables']
        self.sensors = garden_config['sensors']
        self.sensor_garden_mapping = garden_config['sensor_garden_mapping']

        # Prepare data
        self._prepare_data()

    def safe_isna(self, cell):
        # Avoid applying isna to arrays/lists
        if isinstance(cell, (list, np.ndarray)):
            return False
        return pd.isna(cell)
    def _prepare_data(self):
        """Prepare and clean the sampling data"""

        # Extract sensor types from sensor names
        sensor_type_map = {}
        for sensor_id, sensor_info in self.sensors.items():
            if 'Temperature' in sensor_info['name']:
                sensor_type_map[sensor_id] = 'temperature'
            elif 'Moisture' in sensor_info['name']:
                sensor_type_map[sensor_id] = 'moisture'
            elif 'Light' in sensor_info['name']:
                sensor_type_map[sensor_id] = 'light'
            elif 'Humidity' in sensor_info['name']:
                sensor_type_map[sensor_id] = 'humidity'
            elif 'Pump' in sensor_info['name']:
                sensor_type_map[sensor_id] = 'pump'

        # Map sensor types if not already in data
        if 'sensor_type' not in self.df.columns:
            self.df['sensor_type'] = self.df['sensor_id'].map(sensor_type_map)

        # Add garden information to dataframe
        self.df['garden_ids'] = self.df['sensor_id'].map(self.sensor_garden_mapping)
        #Remove Inits
        self.df = self.df[self.df['value'] != 'Init']
        # Expand rows for sensors used in multiple gardens
        expanded_rows = []
        for idx, row in self.df.iterrows():
            if not self.safe_isna(row['garden_ids']) and len(row['garden_ids']) > 0:
                for garden_id in row['garden_ids']:
                    new_row = row.copy()
                    new_row['garden_id'] = garden_id
                    new_row['vegetable_type'] = self.gardens[garden_id]['vegetable_type']
                    new_row['location'] = self.gardens[garden_id]['location']
                    expanded_rows.append(new_row)

        self.expanded_df = pd.DataFrame(expanded_rows)

    def get_optimal_ranges(self, vegetable_type):
        """Get optimal ranges for a specific vegetable"""
        return self.vegetables[vegetable_type]

    def calculate_compliance_score(self, garden_id, time_window_hours=2400000):
        """
        Calculate how well a garden meets its vegetable's optimal conditions

        Args:
            garden_id: ID of the garden to analyze
            time_window_hours: Hours to look back for recent data

        Returns:
            Dictionary with compliance scores and details
        """
        garden = self.gardens[garden_id]
        vegetable_type = garden['vegetable_type']
        optimal_ranges = self.get_optimal_ranges(vegetable_type)

        # Get recent data for this garden
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_data = self.expanded_df[
            (self.expanded_df['garden_id'] == garden_id) &
            (self.expanded_df['timestamp'] >= cutoff_time)
            ]

        compliance_scores = {}
        details = {}

        for sensor_type in ['temperature', 'moisture', 'light', 'humidity']:
            if sensor_type not in optimal_ranges:
                continue

            sensor_data = recent_data[recent_data['sensor_type'] == sensor_type]

            if len(sensor_data) == 0:
                compliance_scores[sensor_type] = None
                details[sensor_type] = {'status': 'No data', 'avg_value': None}
                continue

            optimal_min = optimal_ranges[sensor_type]['min']
            optimal_max = optimal_ranges[sensor_type]['max']

            # Calculate percentage of readings within optimal range
            in_range = sensor_data[
                (sensor_data['value'] >= optimal_min) &
                (sensor_data['value'] <= optimal_max)
                ]

            compliance_score = len(in_range) / len(sensor_data) * 100
            avg_value = sensor_data['value'].mean()

            compliance_scores[sensor_type] = compliance_score
            details[sensor_type] = {
                'status': 'Good' if compliance_score >= 80 else 'Needs Attention' if compliance_score >= 60 else 'Poor',
                'avg_value': avg_value,
                'optimal_min': optimal_min,
                'optimal_max': optimal_max,
                'readings_count': len(sensor_data),
                'in_range_count': len(in_range)
            }

        # Overall compliance score
        valid_scores = [score for score in compliance_scores.values() if score is not None]
        overall_score = np.mean(valid_scores) if valid_scores else 0

        return {
            'garden_id': garden_id,
            'vegetable_type': vegetable_type,
            'overall_score': overall_score,
            'individual_scores': compliance_scores,
            'details': details,
            'timestamp': datetime.now()
        }

    def generate_garden_report(self, garden_id):
        """Generate a detailed report for a specific garden"""
        compliance = self.calculate_compliance_score(garden_id)
        garden = self.gardens[garden_id]

        print(f"\n{'=' * 60}")
        print(f"GARDEN ANALYSIS REPORT")
        print(f"{'=' * 60}")
        print(f"Garden: {garden['name']}")
        print(f"Location: {garden['location']}")
        print(f"Vegetable: {garden['vegetable_type'].title()}")
        print(f"Status: {'Active' if garden['active'] else 'Inactive'}")
        print(f"Overall Compliance Score: {compliance['overall_score']:.1f}%")

        print(f"\n{'SENSOR ANALYSIS':-^60}")
        for sensor_type, details in compliance['details'].items():
            if details['avg_value'] is not None:
                print(f"\n{sensor_type.title()}:")
                print(f"  Current Average: {details['avg_value']:.1f}")
                print(f"  Optimal Range: {details['optimal_min']:.1f} - {details['optimal_max']:.1f}")
                print(f"  Compliance: {compliance['individual_scores'][sensor_type]:.1f}%")
                print(f"  Status: {details['status']}")
                print(f"  Readings: {details['in_range_count']}/{details['readings_count']} in range")

        return compliance

    def plot_garden_compliance_overview(self, figsize=(15, 10)):
        """Create overview plots for all active gardens"""
        active_gardens = [g_id for g_id, g in self.gardens.items() if g['active']]

        if not active_gardens:
            print("No active gardens found!")
            return

        # Calculate compliance scores for all gardens
        compliance_data = []
        for garden_id in active_gardens:
            comp = self.calculate_compliance_score(garden_id)
            compliance_data.append(comp)

        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle('Garden Compliance Overview', fontsize=16, fontweight='bold')

        # 1. Overall compliance scores
        garden_names = [self.gardens[comp['garden_id']]['name'] for comp in compliance_data]
        overall_scores = [comp['overall_score'] for comp in compliance_data]

        ax1 = axes[0, 0]
        bars = ax1.bar(range(len(garden_names)), overall_scores,
                       color=['green' if score >= 80 else 'orange' if score >= 60 else 'red'
                              for score in overall_scores])
        ax1.set_title('Overall Compliance Scores')
        ax1.set_ylabel('Compliance Score (%)')
        ax1.set_xticks(range(len(garden_names)))
        ax1.set_xticklabels([name.split(' - ')[0] for name in garden_names], rotation=45)
        ax1.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='Good (80%+)')
        ax1.axhline(y=60, color='orange', linestyle='--', alpha=0.5, label='Fair (60%+)')
        ax1.legend()

        # Add value labels on bars
        for bar, score in zip(bars, overall_scores):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f'{score:.1f}%', ha='center', va='bottom')

        # 2. Compliance by sensor type
        sensor_types = ['temperature', 'moisture', 'light', 'humidity']
        compliance_matrix = []

        for comp in compliance_data:
            row = []
            for sensor_type in sensor_types:
                score = comp['individual_scores'].get(sensor_type, 0)
                row.append(score if score is not None else 0)
            compliance_matrix.append(row)

        ax2 = axes[0, 1]
        im = ax2.imshow(compliance_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
        ax2.set_title('Compliance by Sensor Type')
        ax2.set_xticks(range(len(sensor_types)))
        ax2.set_xticklabels([s.title() for s in sensor_types])
        ax2.set_yticks(range(len(garden_names)))
        ax2.set_yticklabels([name.split(' - ')[0] for name in garden_names])

        # Add text annotations
        for i in range(len(compliance_matrix)):
            for j in range(len(sensor_types)):
                score = compliance_matrix[i][j]
                ax2.text(j, i, f'{score:.0f}%', ha='center', va='center',
                         color='white' if score < 50 else 'black')

        plt.colorbar(im, ax=ax2, label='Compliance Score (%)')

        # 3. Vegetable type distribution
        vegetable_counts = {}
        for comp in compliance_data:
            veg_type = comp['vegetable_type']
            vegetable_counts[veg_type] = vegetable_counts.get(veg_type, 0) + 1

        ax3 = axes[1, 0]
        ax3.pie(vegetable_counts.values(), labels=[v.title() for v in vegetable_counts.keys()],
                autopct='%1.1f%%', startangle=90)
        ax3.set_title('Active Gardens by Vegetable Type')

        # 4. Average sensor readings vs optimal ranges
        ax4 = axes[1, 1]

        # Prepare data for comparison plot
        sensor_comparison_data = []
        for sensor_type in sensor_types:
            for comp in compliance_data:
                if sensor_type in comp['details'] and comp['details'][sensor_type]['avg_value'] is not None:
                    sensor_comparison_data.append({
                        'sensor_type': sensor_type,
                        'garden': self.gardens[comp['garden_id']]['name'].split(' - ')[0],
                        'vegetable': comp['vegetable_type'],
                        'avg_value': comp['details'][sensor_type]['avg_value'],
                        'optimal_min': comp['details'][sensor_type]['optimal_min'],
                        'optimal_max': comp['details'][sensor_type]['optimal_max']
                    })

        if sensor_comparison_data:
            comp_df = pd.DataFrame(sensor_comparison_data)

            # Plot temperature comparison as example
            temp_data = comp_df[comp_df['sensor_type'] == 'temperature']
            if not temp_data.empty:
                x_pos = range(len(temp_data))
                ax4.bar(x_pos, temp_data['avg_value'], alpha=0.7, label='Current Avg')
                optimal_centers = (temp_data['optimal_min'] + temp_data['optimal_max']) / 2
                optimal_ranges = (temp_data['optimal_max'] - temp_data['optimal_min']) / 2
                ax4.errorbar(x_pos, optimal_centers, yerr=optimal_ranges,
                             fmt='ro', capsize=5, label='Optimal Range')
                ax4.set_title('Temperature: Current vs Optimal')
                ax4.set_ylabel('Temperature (°C)')
                ax4.set_xticks(x_pos)
                ax4.set_xticklabels(temp_data['garden'], rotation=45)
                ax4.legend()

        plt.tight_layout()
        plt.show()

        return compliance_data

    def plot_time_series_analysis(self, garden_id, days_back=7, figsize=(15, 12)):
        """Plot time series analysis for a specific garden"""
        garden = self.gardens[garden_id]
        vegetable_type = garden['vegetable_type']
        optimal_ranges = self.get_optimal_ranges(vegetable_type)

        # Get data for the specified time period
        cutoff_time = datetime.now() - timedelta(days=days_back)
        garden_data = self.expanded_df[
            (self.expanded_df['garden_id'] == garden_id) &
            (self.expanded_df['timestamp'] >= cutoff_time)
            ]

        if garden_data.empty:
            print(f"No data found for garden {garden_id} in the last {days_back} days")
            return

        # Create subplots for each sensor type
        sensor_types = garden_data['sensor_type'].unique()
        n_sensors = len(sensor_types)

        fig, axes = plt.subplots(n_sensors, 1, figsize=figsize, sharex=True)
        if n_sensors == 1:
            axes = [axes]

        fig.suptitle(f'Time Series Analysis: {garden["name"]}', fontsize=16, fontweight='bold')

        colors = ['blue', 'green', 'orange', 'red', 'purple']

        for i, sensor_type in enumerate(sensor_types):
            sensor_data = garden_data[garden_data['sensor_type'] == sensor_type]

            # Plot actual values
            axes[i].plot(sensor_data['timestamp'], sensor_data['value'],
                         color=colors[i % len(colors)], linewidth=2, label=f'Actual {sensor_type.title()}')

            # Plot optimal range if available
            if sensor_type in optimal_ranges:
                optimal_min = optimal_ranges[sensor_type]['min']
                optimal_max = optimal_ranges[sensor_type]['max']

                axes[i].axhline(y=optimal_min, color='green', linestyle='--', alpha=0.7, label='Optimal Min')
                axes[i].axhline(y=optimal_max, color='green', linestyle='--', alpha=0.7, label='Optimal Max')
                axes[i].fill_between(sensor_data['timestamp'], optimal_min, optimal_max,
                                     alpha=0.2, color='green', label='Optimal Range')

            axes[i].set_ylabel(f'{sensor_type.title()}')
            axes[i].set_title(f'{sensor_type.title()} Over Time')
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)

        axes[-1].set_xlabel('Time')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def get_irrigation_recommendations(self, garden_id):
        """Generate irrigation recommendations based on current conditions"""
        compliance = self.calculate_compliance_score(garden_id)
        garden = self.gardens[garden_id]
        recommendations = []

        print(f"\n{'IRRIGATION RECOMMENDATIONS':-^60}")
        print(f"Garden: {garden['name']}")

        for sensor_type, details in compliance['details'].items():
            if details['avg_value'] is None:
                recommendations.append(f"⚠️  {sensor_type.title()}: No recent data - check sensors")
                continue

            avg_value = details['avg_value']
            optimal_min = details['optimal_min']
            optimal_max = details['optimal_max']

            if avg_value < optimal_min:
                if sensor_type == 'moisture':
                    recommendations.append(
                        f"💧 Increase irrigation - soil moisture too low ({avg_value:.1f} < {optimal_min})")
                elif sensor_type == 'humidity':
                    recommendations.append(
                        f"💨 Increase humidity - consider misting ({avg_value:.1f}% < {optimal_min}%)")
                elif sensor_type == 'temperature':
                    recommendations.append(
                        f"🌡️  Temperature too low - consider heating ({avg_value:.1f}°C < {optimal_min}°C)")

            elif avg_value > optimal_max:
                if sensor_type == 'moisture':
                    recommendations.append(f"⏸️  Reduce irrigation - soil too wet ({avg_value:.1f} > {optimal_max})")
                elif sensor_type == 'humidity':
                    recommendations.append(
                        f"💨 Improve ventilation - humidity too high ({avg_value:.1f}% > {optimal_max}%)")
                elif sensor_type == 'temperature':
                    recommendations.append(
                        f"🌡️  Temperature too high - consider cooling/shading ({avg_value:.1f}°C > {optimal_max}°C)")

            else:
                recommendations.append(f"✅ {sensor_type.title()} is within optimal range ({avg_value:.1f})")

        if not recommendations:
            recommendations.append("✅ All parameters are within optimal ranges!")

        for rec in recommendations:
            print(f"  {rec}")

        return recommendations


def run(garden_config, database):
    """Run a complete analysis"""

    # Initialize analyzer
    analyzer = IrrigationAnalyzer(garden_config, database)

    # Generate reports for all active gardens
    print("=== IRRIGATION SYSTEM ANALYSIS ===")

    active_gardens = [g_id for g_id, g in analyzer.gardens.items() if g['active']]

    for garden_id in active_gardens:
        analyzer.generate_garden_report(garden_id)
        analyzer.get_irrigation_recommendations(garden_id)
        print("\n" + "=" * 60)

    # Create overview plots FIXME:values issues
    compliance_data = analyzer.plot_garden_compliance_overview()

    # Create time series plot for first garden
    if active_gardens:
        analyzer.plot_time_series_analysis(active_gardens[0])

    return analyzer
