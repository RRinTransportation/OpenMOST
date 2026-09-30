library(shiny)

# Define UI for application
ui <- fluidPage(
  
  # Application title
  titlePanel("Transportation Research Paper Explorer"),
  
  # Sidebar with controls
  sidebarLayout(
    sidebarPanel(
      # Dependent variable selection
      selectInput("dependent_var",
                  "Select Dependent Variable:",
                  choices = c("Code Availability" = "is_code_available",
                              "Data Availability" = "data_multi"),
                  selected = "is_code_available"),
      
      # Independent variable selection
      selectInput("independent_var",
                  "Select Independent Variable:",
                  choices = NULL,  # Will be populated in server
                  selected = NULL)
    ),
    
    # Main panel with outputs
    mainPanel(
      # Output: Variable type indicator
      verbatimTextOutput("var_type_info"),
      
      # Conditional output: Histogram for numeric variables
      conditionalPanel(
        condition = "output.is_numeric == true",
        plotOutput("histogram")
      ),

      # Conditional output: Cross-tabulation for categorical variables
      conditionalPanel(
        condition = "output.is_numeric == false",
        tableOutput("crosstab")
      ),
      
      # Output: Statistical test results
      tableOutput("test_results"),

      # Output: test notes
      textOutput("test_notes")

    )
  )
)

