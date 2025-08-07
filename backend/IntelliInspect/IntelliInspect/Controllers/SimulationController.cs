using Microsoft.AspNetCore.Mvc;
using System.Text;
using System.Text.Json;
using CsvHelper;
using System.Globalization;
using IntelliInspect.Models;
using System.IO;


public class SimulationController : ControllerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IWebHostEnvironment _env;
    private readonly ILogger<SimulationController> _logger;

    public SimulationController(IHttpClientFactory httpClientFactory, IWebHostEnvironment env, ILogger<SimulationController> logger)
    {
        _httpClientFactory = httpClientFactory;
        _env = env;
        _logger = logger;
    }
    private static float GetMockValue(float baseValue, float range)
    {
        var rand = new Random();
        return (float)(baseValue + rand.NextDouble() * range * 2 - range);
    }

    [HttpGet("start")]
    public async Task StartSimulation()
    {
        var response = Response;
        response.Headers.Add("Content-Type", "text/event-stream");

        var appDataPath = Path.Combine(_env.ContentRootPath, "App_Data");

        // Load simulation range
        var rangePath = Path.Combine(appDataPath, "ranges.json");
        if (!System.IO.File.Exists(rangePath))
        {
            response.StatusCode = 404;
            await response.Body.FlushAsync();
            return;
        }

        var rangeJson = await System.IO.File.ReadAllTextAsync(rangePath);
        var simRange = JsonSerializer.Deserialize<SimulationRange>(rangeJson);

        // Load and filter CSV
        var csvPath = Path.Combine(appDataPath, "processed.csv");
        if (!System.IO.File.Exists(csvPath))
        {
            response.StatusCode = 404;
            await response.Body.FlushAsync();
            return;
        }

        using var reader = new StreamReader(csvPath);
        using var csv = new CsvHelper.CsvReader(reader, CultureInfo.InvariantCulture);
        var records = csv.GetRecords<dynamic>()
                        .Where(r =>
                        {
                            var timestampStr = r.synthetic_timestamp;
                            return DateTime.TryParse(timestampStr, out DateTime ts) &&
                                   ts >= simRange.SimStart && ts <= simRange.SimEnd;
                        })
                        .ToList();

        var client = _httpClientFactory.CreateClient();
        client.BaseAddress = new Uri("http://localhost:8000");

        foreach (var record in records)
        {
            var json = JsonSerializer.Serialize(record);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var res = await client.PostAsync("/api/predict", content);
            var responseString = await res.Content.ReadAsStringAsync();
            var result = JsonSerializer.Deserialize<PredictionResult>(responseString);

            if (result == null)
            {
                _logger.LogWarning("Failed to deserialize prediction result: {Response}", responseString);

                continue;
            }

            // Add real-time timestamp
            result.Timestamp = DateTime.UtcNow;

            // Add mocked telemetry data
            result.Temperature = GetMockValue(20, 5);
            result.Pressure = GetMockValue(1010, 10);
            result.Humidity = GetMockValue(60, 15);

            _logger.LogInformation("Prediction: {Id} {Prediction} {Confidence}", result.Id, result.Prediction, result.Confidence);


            // Stream to frontend
            var eventData = $"data: {JsonSerializer.Serialize(result)}\n\n";
            var eventBytes = Encoding.UTF8.GetBytes(eventData);

            await response.Body.WriteAsync(eventBytes);
            await response.Body.FlushAsync();
            await Task.Delay(1000);
        }
    }

}
