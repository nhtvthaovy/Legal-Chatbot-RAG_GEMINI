# XÂY DỰNG CHATBOT TÍCH HỢP RAG VÀ MÔ HÌNH GEMINI TRONG LĨNH VỰC PHÁP LUẬT VIỆT NAM


### Backend
cd backend
python app.py

### Frontend
cd frontend
npm run dev

# Legal Chatbot Project

## Overview
This project, developed by **Vy** at the Vietnam Aviation Academy, Faculty of Information Technology, aims to create a **Legal Chatbot** that integrates **Retrieval-Augmented Generation (RAG)** and the **Gemini model** to deliver accurate and contextually relevant legal consultation based on Vietnamese legal documents. The system is designed to assist a wide range of users, including citizens, businesses, legal professionals, and government agencies, in accessing and understanding legal information efficiently.

The chatbot combines advanced technologies such as **ReactJS** for the frontend, **Flask** for the backend, **ChromaDB** for vector-based data retrieval, **MongoDB** for conversation history storage, and **Gemini** for natural language processing. It supports both guest and authenticated users with features like conversation history management, voice input, and a user-friendly interface.

## Features
1. **Legal Question Handling**:
   - Users can ask legal questions, and the chatbot retrieves relevant legal documents from ChromaDB using RAG and generates precise responses via the Gemini model.
   - Responses include references to legal documents with links for transparency and reliability.

2. **User Authentication**:
   - Supports user registration and login for personalized experiences.
   - Authenticated users can save, manage, and review conversation histories.

3. **Conversation Management**:
   - Users can create, edit, or delete conversations.
   - Conversation history is stored in MongoDB for authenticated users, ensuring dialogue continuity.

4. **Voice Input**:
   - Integrated speech-to-text functionality allows users to input questions via voice, enhancing accessibility.

5. **Responsive Interface**:
   - Built with ReactJS and styled using Tailwind CSS, the interface is intuitive and optimized for both desktop and mobile devices.
   - Features dynamic navigation, interactive chat areas, and legal document references.

6. **Legal Database**:
   - A comprehensive legal database built with MySQL, containing Vietnamese legal documents (VBPL) scraped using BeautifulSoup and managed with Peewee ORM and SQLAlchemy.
   - ChromaDB stores vectorized legal data for efficient semantic search.

7. **Performance Evaluation**:
   - The system was evaluated for retrieval quality (75% average) and response quality (91.3% average).
   - Compared against Llama-3.3-70B-Instruct-Turbo, achieving superior response quality (92.61% vs. 80%) at the cost of slightly longer processing time (8s vs. 2.48s).

## Technologies Used
- **Frontend**:
  - **ReactJS**: For building a dynamic and responsive user interface.
  - **Tailwind CSS**: For utility-first styling and rapid UI development.
- **Backend**:
  - **Flask**: For handling API requests and integrating with AI models.
  - **Python**: Core language for backend logic, data processing, and AI integration.
- **AI and Data Processing**:
  - **Retrieval-Augmented Generation (RAG)**: Combines information retrieval with text generation for accurate responses.
  - **Gemini**: Advanced language model for natural language understanding and generation.
  - **ChromaDB**: Vector database for efficient storage and retrieval of legal documents.
  - **MongoDB**: NoSQL database for storing user data and conversation history.
- **Data Collection**:
  - **BeautifulSoup, SQLAlchemy, Peewee ORM**: For scraping and managing legal data.
  - **Pandas**: For data processing and analysis.

