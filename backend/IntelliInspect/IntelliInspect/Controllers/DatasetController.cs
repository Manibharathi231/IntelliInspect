using CsvHelper;
using CsvHelper.Configuration;
using Microsoft.AspNetCore.Mvc;
using System.Globalization;
using IntelliInspect.Models;
using System.Text.Json;
using System;
using System.Text;
using System.IO;
using System.Threading.Tasks;

namespace IntelliInspect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class DatasetController : ControllerBase
    {
        [HttpPost("upload")]
        [RequestSizeLimit(2_147_483_647)]
        [Consumes("multipart/form-data")]
        public async Task<IActionResult> UploadDataset(IFormFile file)
        {
            if (file == null || file.Length == 0)
                return BadRequest("No file provided.");

            if (!file.FileName.EndsWith(".csv", StringComparison.OrdinalIgnoreCase))
                return BadRequest("Invalid file format. Only .csv files are accepted.");

            var config = new CsvConfiguration(CultureInfo.InvariantCulture)
            {
                PrepareHeaderForMatch = args => args.Header.ToLower(),
                MissingFieldFound = null,
                BadDataFound = null
            };

            int totalRows = 0;
            int totalCols = 0;
            int passCount = 0;
            DateTime baseTime = new DateTime(2021, 1, 1, 0, 0, 0);
            string firstTimestamp = "", lastTimestamp = "";

            var outputDir = Path.Combine(Directory.GetCurrentDirectory(), "App_Data");
            Directory.CreateDirectory(outputDir);
            var outputPath = Path.Combine(outputDir, "processed.csv");

            using var reader = new StreamReader(file.OpenReadStream());
            using var csvReader = new CsvReader(reader, config);

            using var writer = new StreamWriter(outputPath);
            using var csvWriter = new CsvWriter(writer, config);

            // Read header
            csvReader.Read();
            csvReader.ReadHeader();
            var headers = csvReader.HeaderRecord.Select(h => h.ToLower()).ToList();
            bool hasTimestamp = headers.Contains("synthetic_timestamp");

            if (!headers.Contains("response"))
                return BadRequest("The uploaded file does not contain a 'Response' column.");

            if (!hasTimestamp)
                headers.Add("synthetic_timestamp");

            // Write updated header
            foreach (var header in headers)
                csvWriter.WriteField(header);
            csvWriter.NextRecord();

            // Process each row
            while (csvReader.Read())
            {
                var row = csvReader.GetRecord<dynamic>() as IDictionary<string, object>;

                totalRows++;
                if (totalCols == 0)
                    totalCols = row.Count + (hasTimestamp ? 0 : 1);

                string timestamp = hasTimestamp
                    ? row["synthetic_timestamp"].ToString()
                    : baseTime.AddSeconds(totalRows - 1).ToString("yyyy-MM-dd HH:mm:ss");

                if (!hasTimestamp)
                    row["synthetic_timestamp"] = timestamp;

                if (string.IsNullOrEmpty(firstTimestamp)) firstTimestamp = timestamp;
                lastTimestamp = timestamp;

                if (row["response"]?.ToString() == "1")
                    passCount++;

                foreach (var header in headers)
                {
                    row.TryGetValue(header, out var value);
                    csvWriter.WriteField(value);
                }
                csvWriter.NextRecord();
            }

            double passRate = (double)passCount / totalRows * 100;

            return Ok(new
            {
                fileName = file.FileName,
                totalRows,
                totalCols,
                passRate = $"{passRate:F2}%",
                dateRange = $"{firstTimestamp} to {lastTimestamp}"
            });
        }
        [HttpPost("validate-date-ranges")]
        public IActionResult ValidateDateRanges([FromBody] DateRangeRequest request)
        {
            
            var filePath = Path.Combine(Directory.GetCurrentDirectory(), "App_Data", "processed.csv");
            if (!System.IO.File.Exists(filePath))
                return BadRequest("No processed dataset found. Upload the dataset first.");

            var config = new CsvConfiguration(CultureInfo.InvariantCulture)
            {
                PrepareHeaderForMatch = args => args.Header.ToLower(),
                MissingFieldFound = null,
                BadDataFound = null
            };

            // Parse user input
            if (!DateTime.TryParse(request.TrainStart, out var trainStart) ||
                !DateTime.TryParse(request.TrainEnd, out var trainEnd) ||
                !DateTime.TryParse(request.TestStart, out var testStart) ||
                !DateTime.TryParse(request.TestEnd, out var testEnd) ||
                !DateTime.TryParse(request.SimStart, out var simStart) ||
                !DateTime.TryParse(request.SimEnd, out var simEnd))
            {
                return BadRequest("Invalid date format.");
            }

            // Logical order validation
            if (trainEnd >= testStart || testEnd >= simStart)
                return BadRequest("Date ranges must be non-overlapping and in order: Train < Test < Sim.");

            int trainCount = 0, testCount = 0, simCount = 0;
            DateTime minTimestamp = DateTime.MaxValue, maxTimestamp = DateTime.MinValue;

            using var reader = new StreamReader(filePath);
            using var csv = new CsvReader(reader, config);
            csv.Read();
            csv.ReadHeader();

            while (csv.Read())
            {
                if (!csv.TryGetField("synthetic_timestamp", out string timestampStr)) continue;

                if (!DateTime.TryParse(timestampStr, out DateTime ts)) continue;

                // Track overall min/max timestamps
                if (ts < minTimestamp) minTimestamp = ts;
                if (ts > maxTimestamp) maxTimestamp = ts;

                if (ts >= trainStart && ts <= trainEnd) trainCount++;
                else if (ts >= testStart && ts <= testEnd) testCount++;
                else if (ts >= simStart && ts <= simEnd) simCount++;
            }

            // Check if user-specified ranges fall within the file’s range
            if (trainStart < minTimestamp || simEnd > maxTimestamp)
                return BadRequest($"Selected date ranges must be within dataset range: {minTimestamp} to {maxTimestamp}");


            Directory.CreateDirectory(Path.Combine(Directory.GetCurrentDirectory(), "App_Data"));

            var rangePath = Path.Combine(Directory.GetCurrentDirectory(), "App_Data", "ranges.json");

            var rangesToSave = new
            {
                TrainStart = trainStart,
                TrainEnd = trainEnd,
                TestStart = testStart,
                TestEnd = testEnd,
                SimStart = simStart,
                SimEnd = simEnd
            };

            var json = JsonSerializer.Serialize(rangesToSave, new JsonSerializerOptions { WriteIndented = true });
            System.IO.File.WriteAllText(rangePath, json);

            return Ok(new
            {
                status = "Valid",
                training = new { count = trainCount, range = $"{trainStart} to {trainEnd}" },
                testing = new { count = testCount, range = $"{testStart} to {testEnd}" },
                simulation = new { count = simCount, range = $"{simStart} to {simEnd}" },
                overall = new { earliest = minTimestamp, latest = maxTimestamp }
            });
        }

    }

}
