# Calebsons Cloud Serverless — Event-Driven Architecture

## Overview
A serverless event-driven system using AWS Lambda, DynamoDB, EventBridge, and Step Functions.

## Tech Stack
- AWS Lambda
- DynamoDB
- EventBridge
- Step Functions
- CDK

## Features
- Event orchestration
- Serverless compute
- Durable workflows
- Scalable design

## Architecture
```mermaid
flowchart TD
    PRODUCER[Event Producers] --> BUS[EventBridge]
    BUS --> L1[Lambda Function A]
    BUS --> L2[Lambda Function B]
    L1 --> DB[DynamoDB]
    L2 --> DB
    BUS --> STEP[Step Functions Workflow]
    STEP --> DB
    CDK[AWS CDK Infra] -.-> BUS
```

## Setup
    cd infra
    npm install
    cdk deploy

## Deployment
- AWS CDK

## Roadmap
- Add analytics pipeline
- Add retry policies
