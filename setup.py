from setuptools import setup, find_packages

setup(
    name='pose_estimation_app',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'opencv-python',
        'ultralytics',
        'python-osc',
        'Pillow',
        'numpy',
        'pygrabber'
    ],
    entry_points={
        'console_scripts': [
            'pose-estimation=webcam_pose_estimation:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['yolov8n-pose.pt'],
    },
) 