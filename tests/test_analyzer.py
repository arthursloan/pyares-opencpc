#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: /tests/test_analyzer.py
# Project: pyares-opencpc
# Created Date: Tuesday, April 14th 2026, 5:59:53 pm
# Author(s): Arthur W. N. Sloan
# -----
# MIT License
# 
# Copyright (c) 2026 Arthur Sloan
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
###

from PyAres import AresAnalyzerService, AnalysisRequest, Analysis, AresDataType, Outcome

def analyze(request: AnalysisRequest) -> Analysis:
    #Custom Analysis Logic
    value = request.inputs.get("Analyzer_Input")

    print(f"Recevied Value: {value}")

    analysis = Analysis(result=value, outcome=Outcome.SUCCESS)
    return analysis


if __name__ == "__main__":
    #Basic details about your analyzer
    name = "PyAres OpenCPC Testing And Development Analyzer"
    version = "1.0.0"
    description = "Takes in single values and passes them back to ARES for "
    DemoAnalyzer = AresAnalyzerService(analyze, name, version, description,port=7102)

    #Add Analysis Parameters
    DemoAnalyzer.add_analysis_parameter("Analyzer_Input", AresDataType.NUMBER)
    DemoAnalyzer.start()