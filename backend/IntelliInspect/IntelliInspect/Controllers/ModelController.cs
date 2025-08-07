using Microsoft.AspNetCore.Mvc;
using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace IntelliInspect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ModelController : ControllerBase
    {
        private readonly IHttpClientFactory _httpClientFactory;

        public ModelController(IHttpClientFactory httpClientFactory)
            => _httpClientFactory = httpClientFactory;

        [HttpGet("train")]
        public async Task<IActionResult> TrainModel()
        {
            var dataDir = Path.Combine(Directory.GetCurrentDirectory(), "App_Data");
            var csvPath = Path.Combine(dataDir, "processed.csv");
            var rangesPath = Path.Combine(dataDir, "ranges.json");

            if (!System.IO.File.Exists(csvPath) || !System.IO.File.Exists(rangesPath))
                return BadRequest("Missing processed.csv or ranges.json; complete Steps 1 & 2 first.");

            // Open the CSV file as a stream (no in-memory byte array)
            using var fileStream = System.IO.File.OpenRead(csvPath);

            // Read the ranges JSON into memory (small)
            var rangesJson = await System.IO.File.ReadAllTextAsync(rangesPath);

            // Build multipart/form-data content
            using var content = new MultipartFormDataContent();
            // Stream the CSV file
            var fileContent = new StreamContent(fileStream);
            fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("text/csv");
            content.Add(fileContent, "file", "processed.csv");

            // Add ranges JSON
            content.Add(new StringContent(rangesJson, Encoding.UTF8, "application/json"), "ranges");

            // Call the FastAPI service
            var client = _httpClientFactory.CreateClient();
            client.Timeout = TimeSpan.FromMinutes(10);

            var response = await client.PostAsync("http://localhost:8000/api/train-model", content);
            if (!response.IsSuccessStatusCode)
            {
                var err = await response.Content.ReadAsStringAsync();
                return StatusCode((int)response.StatusCode, $"ML service error: {err}");
            }

            // Forward the metrics JSON
            var metricsJson = await response.Content.ReadAsStringAsync();
            var metrics = JsonSerializer.Deserialize<JsonElement>(metricsJson);
            return Ok(metrics);
        }
    }
}
