# from fastapi import HTTPException, Header, status
# from fastapi.responses import JSONResponse
# from google import 
# import os

# from schemas.genai_schema import PreparationBody, GenAIResponse, PromptBody
# from utils.helper_utils import HelperUtils

# utils = HelperUtils()


# class GenerativeAI:
#     def __init__(self):
#         pass
    
#     def preparation_instructions(self, preparation_body: PreparationBody, authorization: str = Header(...)):
#         """Generate preparation instructions based on user input."""

#         try:
#             # Validate Authorization Header
#             if not authorization.startswith("Bearer "):
#                 raise HTTPException(
#                     status_code=status.HTTP_403_FORBIDDEN,
#                     detail="Authorization header must start with 'Bearer '"
#                 )

#             # Validate JWT
#             token = authorization[7:]
#             utils.validate_JWT(token)
            
#             # Configure the API key
#             genai.configure(api_key=os.getenv("API_KEY"))            
#             prompt = f"You are a helpful cooking assistant. Provide detailed preparation instructions for the following foods: {preparation_body.food_list}."
            
#             # Use the correct model name (check Google's documentation for available models)
#             model = genai.GenerativeModel('gemini-2.5-flash')
#             response = model.generate_content(prompt)
            
#             print(type(response.text))
            
#             return {
#                 "status": "success",
#                 "message": "Preparation instructions generated successfully",
#                 "payload": response.text
#             }
            
#         except Exception as e:
#             print(e)
#             return JSONResponse(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 content=GenAIResponse(
#                     status="error",
#                     message="Error when generating preparation instructions",
#                     payload=str(e)
#                 ).dict()
#             )
    
#     def generate_custom_recipe(self, prompt_body: PromptBody, authorization: str = Header(...)):
#         """Generate a custom recipe based on user input."""

#         try:
#             # Validate Authorization Header
#             if not authorization.startswith("Bearer "):
#                 raise HTTPException(
#                     status_code=status.HTTP_403_FORBIDDEN,
#                     detail="Authorization header must start with 'Bearer '"
#                 )

#             # Validate JWT
#             token = authorization[7:]
#             utils.validate_JWT(token)
            
#             # Configure the API key
#             genai.configure(api_key=os.getenv("API_KEY"))
            
#             food_list = prompt_body.food_list
#             spices = prompt_body.spices
#             narrative = prompt_body.narrative
            
#             prompt = (
#                 "You are a meal assistant. Respond in a JSON with key value pair: recipe, "
#                 "name, ingredients and instructions in steps. "
#                 f"Given the following list of foods: {food_list} and the following spices: {spices}. "
#                 f"Create a recipe that follows this narrative: {narrative}"
#             )

#             model = genai.GenerativeModel('gemini-3-pro-preview')
#             response = model.generate_content(prompt)
            
#             return {
#                 "status": "success",
#                 "message": "Recipe generated successfully",
#                 "payload": response.text
#             }
            
#         except Exception as e:
#             return JSONResponse(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 content=GenAIResponse(
#                     status="error",
#                     message="Error when generating custom recipe",
#                     payload=str(e)
#                 ).dict()
#             )