using System.Text.Json.Serialization;

public class PredictionResult
{
    [JsonPropertyName("SampleId")]
    public string Id { get; set; }
    public string Prediction { get; set; }
    public double Confidence { get; set; }
    public DateTime Timestamp { get; set; }

    public float Temperature { get; set; }
    public float Pressure { get; set; }
    public float Humidity { get; set; }
}
